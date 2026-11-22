from src.prepare_data import W_ONE_WAY, W_RECIPROCAL, reciprocity_weights


def test_reciprocity_weights():
    # ids da LCC 0,1,2 correspondem aos ids originais 10, 20, 30
    original = [10, 20, 30]
    directed = [(10, 20), (20, 10), (20, 30)]  # 10<->20 recíproco; 20->30 mão única
    edges = [(0, 1), (1, 2)]
    assert reciprocity_weights(edges, original, directed) == [W_RECIPROCAL, W_ONE_WAY]
    assert (W_RECIPROCAL, W_ONE_WAY) == (1, 2)
