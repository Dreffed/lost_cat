import logging
import os
import sys
from lost_cat.lost_cat import LostCat
from lost_cat.utils.path_utils import build_path, get_filename

# setup the logger
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# set up the paths
paths = []
paths.append(os.path.join("D:\\", "users", "ms", "MSO - thoughtswinsystems.com", "OneDrive - thoughtswinsystems.com", "Sample Data"))
paths.append(get_filename({'root':'.', 'folders':['tests', 'data']}))

for p_uri in paths:
    logger.info(p_uri)
    b_obj = build_path(p_uri)
    logger.info(b_obj)

l_cat = LostCat()
for idx, p_uri in enumerate(paths):
    l_cat.add_source(label=idx, uri=p_uri)

res_obj = l_cat.catalog_artifacts()
logger.info(res_obj)

