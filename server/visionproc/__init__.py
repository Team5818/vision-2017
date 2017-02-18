import cv2

from ..dataclasses import Configuration, ConfigMode


def process_image(cfg_id: ConfigMode, cfg: Configuration, image) -> int:
    # Grab frame
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Remove Small Particles
    mask = cv2.inRange(hsv, cfg.lower_thresh, cfg.upper_thresh)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    if cfg_id == ConfigMode.TAPE:
        if len(cnts) > 0:
            x_center = 160
            cnts = sorted(cnts, key=cv2.contourArea)
            (x, y, w, h) = cv2.boundingRect(cnts[-1])
            if len(cnts) < 2:
                (x2, y2, w2, h2) = (0, 0, 0, 0)
            else:
                (x2, y2, w2, h2) = cv2.boundingRect(cnts[-2])
            if w * h > 50 and w2 * h2 > 50:
                cv2.rectangle(image, (int(min(x, x2)), int(max(y, y2))),
                              (int(max(x + w, x2 + w2)),
                               int(min(y + h, y2 + h2))), (0, 0, 255), 2)
                x_center = int((min(x, x2) + max(x + w, x2 + w2)) / 2)
                y_center = int((min(y, y2) + max(y + h, y2 + h2)) / 2)
                cv2.circle(image, (x_center, y_center), 3, (0, 0, 255), 2)
            elif max(w * h, w2 * h2) > 50:
                cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)),
                              (0, 0, 255), 2)
                x_center = int(x + w / 2)
                y_center = int(y + h / 2)
                cv2.circle(image, (x_center, y_center), 3, (0, 0, 255), 2)
        else:
            x_center = 160
    else:
        if len(cnts) > 0:
            x_center = 160
            c = max(cnts, key=cv2.contourArea)
            if len(c) > 5:
                rect = cv2.minAreaRect(c)
                ((x, y), (w, h), ang) = rect
                if w * h > 100:
                    cv2.ellipse(image, rect, (0, 255, 255), 2)
                    cv2.circle(image, (int(x), int(y)), 3, (0, 255, 0), 2)
                    x_center = x
        else:
            x_center = 160

    return x_center
