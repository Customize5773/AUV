// Offline FBX conversion only; Gazebo loads the generated OBJ asset.
#include <assimp/Importer.hpp>
#include <assimp/Exporter.hpp>
#include <assimp/postprocess.h>
#include <iostream>
int main(int argc, char **argv) {
  if (argc != 3) { std::cerr << "Usage: export_auv_fbx input.fbx output.glb\n"; return 2; }
  Assimp::Importer importer;
  const auto scene = importer.ReadFile(argv[1], aiProcess_Triangulate |
      aiProcess_PreTransformVertices | aiProcess_JoinIdenticalVertices | aiProcess_GenNormals);
  if (!scene) { std::cerr << importer.GetErrorString(); return 1; }
  Assimp::Exporter exporter;
  if (exporter.Export(scene, "glb2", argv[2]) != AI_SUCCESS) {
    std::cerr << exporter.GetErrorString(); return 1;
  }
}
