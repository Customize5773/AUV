from check_arena import payload_retained


def test_retention_accepts_joint_or_bilateral_contact_with_independent_confirmation():
    result = {'payload_retrieved': True}
    released = {'payload': {'released': True, 'position': [0., 0., -.04]}}
    frame = dict(balls=released, pickup_position=[0., 0., 0.])
    for mechanism in ('payload_attached', 'unlatched_bilateral_grip'):
        held = {**frame, mechanism: True}
        assert payload_retained([held], result)
        assert not payload_retained([held], {})
        assert not payload_retained([held, frame], result)
        assert not payload_retained([{**held, 'pickup_position': [1., 0., 0.]}], result)
        assert not payload_retained([{**held, 'balls': {}}], result)
    assert not payload_retained([], result)
