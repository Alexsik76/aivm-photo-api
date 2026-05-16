import pytest
import numpy as np
from app.ml.postprocess import class_agnostic_nms, group_into_rows, assemble_number

def test_class_agnostic_nms():
    # Two overlapping boxes for the same digit (e.g. '2' and '3')
    boxes = np.array([
        [10, 10, 50, 50],
        [12, 12, 52, 52]
    ])
    scores = np.array([0.9, 0.85])
    classes = np.array([2, 3])
    
    keep_boxes, keep_scores, keep_classes = class_agnostic_nms(boxes, scores, classes, iou_threshold=0.4)
    
    assert len(keep_boxes) == 1
    assert keep_scores[0] == 0.9
    assert keep_classes[0] == 2

def test_group_into_rows():
    # 3 rows of digits
    # Row 0 (SYS): y centers ~20
    # Row 1 (DIA): y centers ~100
    # Row 2 (PUL): y centers ~180
    boxes = np.array([
        [10, 10, 30, 30], [40, 10, 60, 30],  # Row 0: 1, 2
        [10, 90, 30, 110], [40, 90, 60, 110], # Row 1: 7, 5
        [10, 170, 30, 190], [40, 170, 60, 190] # Row 2: 8, 0
    ])
    classes = np.array([1, 2, 7, 5, 8, 0])
    scores = np.array([0.9]*6)
    
    rows = group_into_rows(boxes, classes, scores)
    
    assert len(rows) == 3
    assert "".join(map(str, rows[0]['classes'].astype(int))) == "12"
    assert "".join(map(str, rows[1]['classes'].astype(int))) == "75"
    assert "".join(map(str, rows[2]['classes'].astype(int))) == "80"

def test_assemble_number():
    row_data = {
        'classes': np.array([1, 2, 5]),
        'scores': np.array([0.9, 0.8, 0.7])
    }
    num, conf = assemble_number(row_data)
    assert num == 125
    assert conf == pytest.approx(0.8)
