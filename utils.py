import re
import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance(db)


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField()
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField()
    mime_type = fields.StrField()
    caption = fields.StrField()

    class Meta:
        collection_name = COLLECTION_NAME


async def save_file(media):
    """Save file in database"""

    file = Media(
        file_id=media.file_id,
        file_ref=media.file_ref,
        file_name=media.file_name,
        file_size=media.file_size,
        file_type=media.file_type,
        mime_type=media.mime_type,
    )

    caption = media.caption
    if caption:
        file.caption = caption

    try:
        await file.commit()
    except DuplicateKeyError:
        logger.warning(media.file_name + " filmlar omboriga saqlangan")
    else:
        logger.info(media.file_name + " filmlar omboriga saqland")


async def get_search_results(query, file_type=None, max_results=10, offset=0):
    """For given query return (results, next_offset)"""

    raw_pattern = query.lower().strip().replace(' ', '.?')
    if not raw_pattern:
        raw_pattern = '.'

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    filter = {'file_name': regex}
    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    results = await Media.find(filter).sort(
        '$natural', -1).skip(offset).limit(max_results).to_list(length=max_results)
    return results, next_offset
