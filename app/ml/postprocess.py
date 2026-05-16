import numpy as np
from sklearn.cluster import KMeans

def class_agnostic_nms(boxes, scores, classes, iou_threshold=0.4):
    """
    Perform class-agnostic Non-Maximum Suppression.
    boxes: nx4 (x1, y1, x2, y2)
    scores: n
    classes: n
    """
    if len(boxes) == 0:
        return np.array([]), np.array([]), np.array([])

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= iou_threshold)[0]
        order = order[inds + 1]

    return boxes[keep], scores[keep], classes[keep]

def group_into_rows(boxes, classes, scores):
    """
    Group detected digits into 3 rows using K-Means on Y-coordinates.
    """
    if len(boxes) < 3:
        return None
        
    y_centers = (boxes[:, 1] + boxes[:, 3]) / 2
    y_centers_2d = y_centers.reshape(-1, 1)
    
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto').fit(y_centers_2d)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_.flatten()
    
    # Sort clusters by Y-coordinate to identify SYS, DIA, PUL
    row_indices = np.argsort(centers)
    
    rows = []
    for row_idx in row_indices:
        mask = (labels == row_idx)
        row_boxes = boxes[mask]
        row_classes = classes[mask]
        row_scores = scores[mask]
        
        # Sort by X-coordinate
        x_sort_idx = np.argsort(row_boxes[:, 0])
        rows.append({
            'classes': row_classes[x_sort_idx],
            'scores': row_scores[x_sort_idx]
        })
        
    return rows

def assemble_number(row_data):
    """Concatenate digits to form a number."""
    if not row_data['classes'].size:
        return 0, 0.0
    
    num_str = "".join(map(str, row_data['classes'].astype(int)))
    avg_conf = np.mean(row_data['scores'])
    return int(num_str), avg_conf
