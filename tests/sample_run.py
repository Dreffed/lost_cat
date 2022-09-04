import logging
import os
import sys
from lost_cat.lost_cat import LostCat
from lost_cat.utils.path_utils import build_path, get_filename

# setup the logger
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# check the catalog artifacts - Modality
# 'Modality' -> 'BodyPartExamined' -> 'PhotometricInterpretation' -> 'StudyInstanceUID' -> 'SeriesInstanceUID' -> 'SeriesInstanceUID'
def unroll(node: dict, indent: int = 0, max_depth: int = 4):
    """simple unroller"""
    pad = "\t"*indent

    if indent >= max_depth or not node:
        print(f"{pad}{node}")
        return

    if isinstance(node, dict):
        for k,v in node.items():
            print(f"{pad}{k}")
            unroll(v, indent+1)

    elif isinstance(node, list):
        l = len(node)
        print(f"{pad}{l}")
    else:
        print(f"{pad}{node}")

# set up the paths
paths = []
#paths.append(get_filename({'root':'.', 'folders':['tests', 'data']}))
#paths.append(get_filename({"root":"C:\\", "folders": ["users", "ms", "Documents"]}))
paths.append(get_filename({"root":"C:\\", "folders": ["users", "ms", "Documents"]}))

paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Documents"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Pictures"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Gallery"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Dropbox"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Music"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "Videos"]}))
paths.append(get_filename({"root":"D:\\", "folders": ["users", "ms", "OneDrive"]}))

paths.append(get_filename({"root":"E:\\", "folders": ["users", "ms", "Documents"]}))
paths.append(get_filename({"root":"E:\\", "folders": ["users", "ms", "Pictures"]}))
paths.append(get_filename({"root":"E:\\", "folders": ["users", "ms", "ebooks"]}))
paths.append(get_filename({"root":"E:\\", "folders": ["users", "ms", "google"]}))
#paths.append(get_filename({"root":"%HOME%", "folders": ["OneDrive", "Documents"]}))

for p_uri in paths:
    b_obj = build_path(p_uri)
    logger.info(b_obj)

l_cat = LostCat(shelve_paths={"artifacts":"E:\\users\\ms\\git\\Dreffed\\lost_cat\\data\\artifacts"})
logger.info(l_cat._paths)

for idx, p_uri in enumerate(paths):
    l_cat.add_source(label=idx, uri=p_uri)
    logger.info("Adding source: %s", p_uri)

res_obj = l_cat.catalog_artifacts()
logger.info(res_obj)

logger.debug("Artifacts: %s", len(l_cat._artifacts.get("files",{})))

cat_obj = l_cat.process_parsers()
logger.info(cat_obj)

l_cat.close()
