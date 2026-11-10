"""Offline preparation of the supplied SAUVC 2027 v1 CAD export (requires trimesh,
and fast-simplification; these are not simulator dependencies).
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intermediate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    scene = trimesh.load(args.intermediate, force='scene', process=False)
    meshes = list(scene.dump())
    center = np.median(np.concatenate([m.vertices[::100] for m in meshes]), axis=0)
    kept, removed, original = [], 0, sum(len(m.faces) for m in meshes)
    for mesh in meshes:
        # This CAD export contains faces near the world origin, far from the assembly.
        valid = np.linalg.norm(mesh.vertices-center, axis=1) < 2000
        mask = valid[mesh.faces].all(axis=1)
        removed += int((~mask).sum())
        mesh.update_faces(mask)
        mesh.remove_unreferenced_vertices()
        if len(mesh.faces):
            kept.append(mesh)
    assert kept and removed > 0, 'unexpected source layout; inspect before conversion'
    bounds = np.array([np.min([m.bounds[0] for m in kept], axis=0),
                       np.max([m.bounds[1] for m in kept], axis=0)])
    origin = bounds.mean(axis=0)
    # Assembly long axis is -Y; provisional nose direction maps to simulator +X.
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    extents = (bounds[1]-bounds[0])[[1, 0, 2]]
    scale = float(np.min(np.array([.6, .4, .2])/extents))
    total = sum(len(m.faces) for m in kept)
    output = trimesh.Scene()
    for index, mesh in enumerate(kept):
        material = mesh.visual.material
        mesh.vertices = (mesh.vertices-origin) @ rotation.T * scale
        mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=6)
        target = max(128, int(100000*len(mesh.faces)/total))
        if len(mesh.faces) > target:
            mesh = mesh.simplify_quadric_decimation(face_count=target)
        normals = np.zeros_like(mesh.vertices)
        faces = mesh.vertices[mesh.faces]
        face_normals = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
        for corner in range(3):
            np.add.at(normals, mesh.faces[:, corner], face_normals)
        lengths = np.linalg.norm(normals, axis=1)
        normals /= np.maximum(lengths[:, None], 1e-15)
        mesh.vertex_normals = normals
        mesh.visual = trimesh.visual.TextureVisuals(material=material)
        output.add_geometry(mesh, geom_name=f'part_{index}', node_name=f'part_{index}')
    assert np.all(output.extents <= np.array([.6, .4, .2])+1e-6)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    from trimesh.exchange.obj import export_obj
    text, materials = export_obj(output, return_texture=True, include_normals=True)
    args.output.write_text(text)
    for name, data in materials.items():
        assert Path(name).name == name
        (args.output.parent/name).write_bytes(data)
    report = dict(source_triangles=original, removed_outlier_triangles=removed,
        output_triangles=sum(len(m.faces) for m in output.geometry.values()),
        source_bounds=bounds.tolist(), source_center=origin.tolist(), scale=scale,
        rotation=rotation.tolist(), output_bounds=output.bounds.tolist(),
        output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        physical_dimensions_calibrated=False, nose_direction_confirmed=False)
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
