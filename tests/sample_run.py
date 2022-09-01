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
def unroll(node: dict, indent: int = 0, max: int = 4):
    """simple unroller"""
    if indent >= max or not node:
        return

    pad = "\t"*indent
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
paths.append(get_filename({'root':'.', 'folders':['tests', 'data']}))
logger.info(paths)

for p_uri in paths:
    logger.info(p_uri)
    b_obj = build_path(p_uri)
    logger.info(b_obj)

l_cat = LostCat()
for idx, p_uri in enumerate(paths):
    l_cat.add_source(label=idx, uri=p_uri)

res_obj = l_cat.catalog_artifacts()
logger.info(res_obj)

cat_obj = l_cat.process_artifacts()
logger.info(cat_obj)


