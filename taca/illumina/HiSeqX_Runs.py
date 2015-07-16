import os
import re
import csv
import glob
import datetime
from taca.illumina.Runs import Run
from flowcell_parser.classes import RunParametersParser, SampleSheetParser, RunParser

import logging

logger = logging.getLogger(__name__)

class HiSeqX_Run(Run):
    
    def __init__(self,  run_dir, samplesheet_folders):
        super(HiSeqX_Run, self).__init__( run_dir, samplesheet_folders)
        self._set_sequencer_type()


    def _set_sequencer_type(self):
        self.sequencer_type = "HiSeqX"



    def _get_samplesheet(self):
        """
            Locate and parse the samplesheet for a run. The idea is that there is a folder in
            samplesheet_folders that contains a samplesheet named flowecell_id.csv.
        """
        current_year = '20' + self.id[0:2]
        samplesheets_dir = os.path.join(self.CONFIG['samplesheets_dir'],
                                                current_year)
        ssname = os.path.join(samplesheets_dir, '{}.csv'.format(self.flowcell_id))
        if os.path.exists(ssname):
            return ssname
        else:
            raise RunTimeError("not able to find samplesheet {}.csv in {}".format(self.flowcell_id, self.CONFIG['samplesheets_dir']))





    def demultiplex_run(self):
        """
           Demultiplex a Xten run:
            - find the samplesheet
            - make a local copy of the samplesheet and name it SampleSheet.csv
            - define if necessary the bcl2fastq commands (if indexes are not of size 8, i.e. neoprep)
            - run bcl2fastq conversion
        """

        ssname   = self._get_samplesheet()
        ssparser = SampleSheetParser(ssname)


        #samplesheet to be positioned in the FC directory with name SampleSheet.csv (Illumina default)
        samplesheet_dest = os.path.join(self.run_dir, "SampleSheet.csv")
        #check that the samplesheet is not already present and generate the dafault SampleSheet. This avoids multiple runs on the same FC
        if os.path.exists(samplesheet_dest):
            logger.warn(("When trying to generate SampleSheet.csv for Flowcell "
                         "{}  looks like that SampleSheet.csv was already "
                         "present in {} !!".format(self.id, samplesheet_dest)))
            return False
        try:
            with open(samplesheet_dest, 'wb') as fcd:
                fcd.write(_generate_clean_samplesheet(ssparser, fields_to_remove=['index2'], rename_samples=True, rename_qPCR_suffix = True, fields_qPCR=['SampleName']))
        except Exception as e:
            logger.error(e.text)
            return False
        ##SampleSheet.csv generated
        import pdb
        pdb.set_trace()
        per_lane_base_mask = self.generate_per_lane_base_mask()
        import pdb
        pdb.set_trace()

def generate_per_lane_base_mask(self):
    """
    This functions generate the base masks for each lane for an HiSeqX run. RunInfo.xml contains the configuration
    that in a X-ten run shoudl always be [Y151,I8,Y151]. However we might:
        - run without indexes
        - run with all lanes with indexes of size 6 (NeoPrep)
        - run some lanes with indexes of a certain size and others of other size
    N.B. this function will fail if the same lane has indexes of different size
    """
    import pdb
    pdb.set_trace()
    #geenrate new ssparser (from the renamed smaplesheet)
    ssparser = SampleSheetParser(os.path.join(self.run_dir, "SampleSheet.csv"))
    runSetup = self.runParserObj.runinfo.get_read_configuration()
    #do more or less what get_base_masks does but with different assumptions









def _generate_clean_samplesheet(ssparser, fields_to_remove=None, rename_samples=True, rename_qPCR_suffix = False, fields_qPCR= None):
    """
        Will generate a 'clean' samplesheet, the given fields will be removed. 
        if rename_samples is True, samples prepended with 'Sample_'  are renamed to match the sample name
    """
    output=""
    if not fields_to_remove:
        fields_to_remove=[]
    #Header
    output+="[Header]{}".format(os.linesep)
    for field in ssparser.header:
        output+="{},{}".format(field.rstrip(), ssparser.header[field].rstrip())
        output+=os.linesep
    #Data
    output+="[Data]{}".format(os.linesep)
    datafields=[]
    for field in ssparser.datafields:
        if field not in fields_to_remove:
            datafields.append(field)
    output+=",".join(datafields)
    output+=os.linesep
    for line in ssparser.data:
        line_ar=[]
        for field in datafields:
            value = line[field]
            if rename_samples and 'SampleID' in field :
                try:
                    if rename_qPCR_suffix and 'SampleName' in fields_qPCR:
                        #substitute SampleID with SampleName, add Sample_ as prefix and remove __qPCR_ suffix
                        value =re.sub('__qPCR_$', '', 'Sample_{}'.format(line['SampleName']))
                    else:
                        #substitute SampleID with SampleName, add Sample_ as prefix
                        value ='Sample_{}'.format(line['SampleName'])
                except:
                        #otherwise add Sample_ as prefix
                        value = 'Sample_{}'.format(line['SampleID'])
            elif rename_qPCR_suffix and field in fields_qPCR:
                value = re.sub('__qPCR_$', '', line[field])
                                                                                                                            
            line_ar.append(value)
                                                                                                                                
        output+=",".join(line_ar)
        output+=os.linesep

    return output

    