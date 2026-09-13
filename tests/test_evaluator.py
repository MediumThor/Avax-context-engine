from packages.evaluator.metrics import brier_score,direction_accuracy,interval_coverage,mae,pinball_loss


def test_metrics():
    assert mae([1,2],[1,3])==0.5
    assert direction_accuracy([1,-1],[0.2,-0.4])==1.0
    assert brier_score([1,0],[1,0])==0.0
    assert interval_coverage([0,1],[-1,0.5],[1,1.5])==1.0
    assert pinball_loss([1],[1],0.5)==0.0
