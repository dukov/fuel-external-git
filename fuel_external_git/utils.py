import os

from nailgun.db import db
from nailgun.db.sqlalchemy.models import Cluster
from nailgun.db.sqlalchemy.models import Release
from nailgun.logger import logger
from fuel_external_git.openstack_config import OpenStackConfig


def get_file_exts_list(resource_mapping):
    res = set()
    for resource in resource_mapping.values():
        res.add(resource['path'].split('.')[-1])
    return res


def get_config_hash(file_dir, resource_mapping, exts=['conf']):
    res = {}
    if not os.path.isdir(file_dir):
        logger.debug(
            "Directory {} not found. Returning emty dict".format(file_dir))
        return {}

    conf_files = [conf for conf in os.listdir(file_dir)
                  if conf.split('.')[-1] in exts]
    for conf_file in conf_files:
        config = OpenStackConfig(os.path.join(file_dir, conf_file),
                                 resource_mapping)
        res[config.config_name] = config.to_config_dict()
    return res


def deep_merge(dct, merge_dct):
    for k, v in merge_dct.iteritems():
        if (k in dct and isinstance(dct[k], dict)):
            deep_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


# TODO (dukov) Remove this ugly staff once extension management is available
def register_extension(ext_name):
    def decorator(cls):
        exts = {cl: cl['extensions'] for cl in
                list(db().query(Cluster).all()) +
                list(db().query(Release).all())}
        save = False
        for obj, extensions in exts.items():
            if u'fuel_external_git' not in extensions:
                extensions.append(u'fuel_external_git')
                extensions = list(set(extensions))
                obj.extensions = extensions
                save = True
                db().flush()

        if save:
            db().commit()
        return cls
    return decorator
