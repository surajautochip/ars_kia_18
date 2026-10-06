import logging
_logger = logging.getLogger(__name__)

from openalpr import Alpr
from argparse import ArgumentParser
import base64

parser = ArgumentParser(description='OpenALPR Python Test Program')

parser.add_argument("-c", "--country", dest="country", action="store", default="in",
                  help="License plate Country" )

parser.add_argument("--config", dest="config", action="store", default="/home/amal/odoo/odoo11/Bitbucket/ac-hyundai-projects/ALPR_PROJECT/config/openalpr.conf.defaults",
                  help="Path to openalpr.conf config file" )

parser.add_argument("--runtime_data", dest="runtime_data", action="store", default="/home/amal/odoo/odoo11/Bitbucket/ac-hyundai-projects/ALPR_PROJECT/runtime_data",
                  help="Path to OpenALPR runtime_data directory" )

parser.add_argument('--plate_image', default="/home/amal/odoo/odoo11/Bitbucket/ac-hyundai-projects/ALPR_PROJECT/src/bindings/python/screen.jpg",
                    help='License plate image file')

options = parser.parse_args()

alpr = None
try:
    alpr = Alpr(options.country, options.config, options.runtime_data,)
    if not alpr.is_loaded():
        _logger.info("Error loading OpenALPR")
    else:
        _logger.info("Using OpenALPR " + alpr.get_version())
        alpr.set_top_n(7)
        alpr.set_default_region("in")
        alpr.set_detect_region(False)
        jpeg_bytes = open(options.plate_image, "rb").read()
        
        results = alpr.recognize_array(jpeg_bytes)
        
        # Uncomment to see the full results structure
        import pprint
        pprint.p_logger.info(results)

        _logger.info("Image size: %dx%d" %(results['img_width'], results['img_height']))
        _logger.info("Processing Time: %f" % results['processing_time_ms'])

        i = 0
        for plate in results['results']:
            i += 1
            _logger.info("Plate #%d" % i)
            _logger.info("   %12s %12s" % ("Plate", "Confidence"))
            for candidate in plate['candidates']:
                prefix = "-"
                if candidate['matches_template']:
                    prefix = "*"

                _logger.info("  %s %12s%12f" % (prefix, candidate['plate'], candidate['confidence']))



finally:
    if alpr:
        alpr.unload()
