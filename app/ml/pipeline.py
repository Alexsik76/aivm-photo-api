import time
import logging
import cv2
import numpy as np
from fastapi import HTTPException
from app.ml.postprocess import class_agnostic_nms, group_into_rows, assemble_number

logger = logging.getLogger("app.ml")

def recognize(image_bytes: bytes, display_model, digit_model) -> dict:
    start_time = time.perf_counter()
    
    # 1. Read image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    # 2. YOLO #1 inference (display detector)
    results_display = display_model(img, conf=0.05, verbose=False)
    if not results_display or len(results_display[0].boxes) == 0:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"[recognize] error: \"display not found\" elapsed_ms={elapsed}")
        raise HTTPException(status_code=422, detail="display not found")
        
    # Take bbox with highest confidence
    display_bbox = results_display[0].boxes[np.argmax(results_display[0].boxes.conf.cpu().numpy())]
    x1, y1, x2, y2 = display_bbox.xyxy[0].cpu().numpy()
    
    # 3. Crop and resize with 3% padding
    h, w = img.shape[:2]
    pad_w = (x2 - x1) * 0.03
    pad_h = (y2 - y1) * 0.03
    
    x1_pad = max(0, int(x1 - pad_w))
    y1_pad = max(0, int(y1 - pad_h))
    x2_pad = min(w, int(x2 + pad_w))
    y2_pad = min(h, int(y2 + pad_h))
    
    cropped = img[y1_pad:y2_pad, x1_pad:x2_pad]
    cropped_resized = cv2.resize(cropped, (400, 480))
    
    # 4. YOLO #2 inference (digit detector)
    results_digits = digit_model(cropped_resized, conf=0.25, verbose=False)
    if not results_digits or len(results_digits[0].boxes) == 0:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"[recognize] error: \"no digits detected\" elapsed_ms={elapsed}")
        raise HTTPException(status_code=422, detail="no digits detected")
        
    boxes = results_digits[0].boxes.xyxy.cpu().numpy()
    scores = results_digits[0].boxes.conf.cpu().numpy()
    classes = results_digits[0].boxes.cls.cpu().numpy()
    
    # 5. Class-agnostic NMS
    boxes, scores, classes = class_agnostic_nms(boxes, scores, classes, iou_threshold=0.4)
    
    # 6. Group into rows
    rows = group_into_rows(boxes, classes, scores)
    if rows is None or len(rows) != 3:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        detail = "got fewer than 3 rows" if rows is None else f"got {len(rows)} rows, need 3"
        logger.error(f"[recognize] error: \"{detail}\" elapsed_ms={elapsed}")
        raise HTTPException(status_code=422, detail=detail)
        
    # 7. Assemble numbers
    sys, sys_conf = assemble_number(rows[0])
    dia, dia_conf = assemble_number(rows[1])
    pul, pul_conf = assemble_number(rows[2])
    
    min_confidence = float(np.min(scores))
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    
    logger.info(f"[recognize] success: sys={sys} dia={dia} pul={pul} conf={min_confidence:.2f} elapsed_ms={elapsed_ms}")
    
    return {
        "sys": sys,
        "dia": dia,
        "pul": pul,
        "confidence": min_confidence,
        "elapsed_ms": elapsed_ms
    }
