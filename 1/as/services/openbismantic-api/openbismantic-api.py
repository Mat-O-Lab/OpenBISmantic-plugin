import json
import subprocess
import tempfile
import traceback
import logger

from ch.systemsx.cisd.openbis.generic.client.web.client.exception import UserFailureException
from ch.ethz.sis.openbis.generic.asapi.v3.dto.sample.fetchoptions import SampleFetchOptions
from ch.ethz.sis.openbis.generic.asapi.v3.dto.sample.fetchoptions import SampleTypeFetchOptions
from ch.ethz.sis.openbis.generic.asapi.v3.dto.property.fetchoptions import PropertyAssignmentFetchOptions
from ch.ethz.sis.openbis.generic.asapi.v3.dto.sample.id import SamplePermId
from ch.ethz.sis.openbis.generic.asapi.v3.dto.property import DataType
from ch.ethz.sis.openbis.generic.server.sharedapi.v3.json import GenericObjectMapper
from java.util import List


property_assignment_fetch_options = PropertyAssignmentFetchOptions()
property_assignment_fetch_options.withPropertyType()


sample_type_fetch_options = SampleTypeFetchOptions()
sample_type_fetch_options.withPropertyAssignmentsUsing(property_assignment_fetch_options)

sample_fetch_options = SampleFetchOptions()
sample_fetch_options.withProperties()
sample_fetch_options.withHistory()
sample_fetch_options.withSampleProperties()
sample_fetch_options.withRegistrator()
sample_fetch_options.withModifier()
sample_fetch_options.withExperiment()
sample_fetch_options.withProject()
sample_fetch_options.withSpace()
sample_fetch_options.withParentsUsing(sample_fetch_options)
sample_fetch_options.withChildrenUsing(sample_fetch_options)
sample_fetch_options.withAttachments()
sample_fetch_options.withDataSets()
sample_fetch_options.withTags()
sample_fetch_options.withTypeUsing(sample_type_fetch_options)


def parse_json(data, format='ntriples', base_url=None):
    with tempfile.NamedTemporaryFile() as f:
        mapper = GenericObjectMapper()
        f.write(mapper.valueToTree(data).toString())
        f.seek(0)
        with tempfile.NamedTemporaryFile() as out_f:
            cmd = ['openbis-json-parser', f.name, '-o', out_f.name, '-f', format]
            if base_url is not None:
                cmd.extend(['-b', base_url])
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise Exception(e.output)
            out_f.seek(0)
            result = out_f.read()
    return result


def recursive_export(context, parameters, seen_perm_ids=()):
    if isinstance(parameters.get('permID'), List):
        perm_ids = tuple(map(lambda e: SamplePermId(e), parameters.get('permID')))
    else:
        perm_ids = (SamplePermId(parameters.get('permID')),)
    seen_perm_ids = seen_perm_ids + perm_ids
    samples = context.applicationService.getSamples(context.sessionToken, perm_ids, sample_fetch_options)
    additional_samples = {}
    for sample_id, sample in samples.items():
        sample_properties = sample.getProperties()
        sample_type = sample.getType()
        for property_assignment in sample_type.getPropertyAssignments():
            property_type = property_assignment.getPropertyType()
            if property_type.getDataType() == DataType.SAMPLE:
                other_perm_id = sample_properties.get(property_type.getCode())
                if other_perm_id is None:
                    continue
                additional_samples.update(recursive_export(context, {'permID': other_perm_id}, seen_perm_ids))
                logger.info(property_type.getCode(), other_perm_id)
    samples.update(additional_samples)
    if parameters.get('format', 'json') != 'json':
        return parse_json(samples, format=parameters.get('format'), base_url=parameters.get('baseURL'))
    return samples


def process(context, parameters):
    method = parameters.get('method')
    try:
        if method == 'recursiveExport':
            return recursive_export(context, parameters)
        else:
            raise UserFailureException('Unknown method: "{}"'.format(method))
    except Exception as e:
        logger.error(traceback.format_exc())
        return {'status': 'FAILED', 'error': str(e), 'traceback': traceback.format_exc()}
