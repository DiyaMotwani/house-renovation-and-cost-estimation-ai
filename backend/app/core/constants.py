PROJECT_STATUS_CREATED = "created"
PROJECT_STATUS_IMAGE_UPLOADED = "image_uploaded"
PROJECT_STATUS_IMAGE_REJECTED = "image_rejected"
PROJECT_STATUS_ZONES_DETECTED = "zones_detected"
PROJECT_STATUS_GENERATION_COMPLETE = "generation_complete"
PROJECT_STATUS_ESTIMATION_COMPLETE = "estimation_complete"
PROJECT_STATUS_REPORT_READY = "report_ready"
PROJECT_STATUS_FAILED = "failed"

IMAGE_TYPE_ORIGINAL = "original"
IMAGE_TYPE_SKETCH = "sketch"
IMAGE_TYPE_GENERATED = "generated"
IMAGE_TYPE_MASK = "mask"

TASK_TYPE_VALIDATE_IMAGE = "validate_image"
TASK_TYPE_GENERATE_RENOVATION = "generate_renovation"

TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# GST on works-contract / construction supply (composite rate). Applied on top
# of the material + labour subtotal to present a realistic payable figure. The
# per-zone catalog rates and the line-item math are unchanged by this.
GST_RATE_PCT = 18.0
