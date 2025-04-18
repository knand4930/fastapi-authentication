# # utils/logger.py
# from models import ActivityLog
# from sqlalchemy.orm import Session
#
# def log_activity(
#     db: Session,
#     user_id: int = None,
#     activity_type: str = "",
#     description: str = "",
#     endpoint: str = "",
#     method: str = "",
#     ip_address: str = ""
# ):
#     log = ActivityLog(
#         user_id=user_id,
#         activity_type=activity_type,
#         description=description,
#         endpoint=endpoint,
#         method=method,
#         ip_address=ip_address,
#     )
#     db.add(log)
#     db.commit()
#     db.refresh(log)
