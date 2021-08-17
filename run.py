import argparse
import sys
import os
import TitaniaTest


def parse_args() -> argparse.Namespace:
    # parse command line argument
    parser = argparse.ArgumentParser(description="Titania Testing")
    parser.add_argument('--output', type=str, default=".", help="\
        Folderpath to store test results. \n \
        Test data includes log file of results and \
        any images captured during the test.")
    parser.add_argument('--capture_rate', type=float, default=1, help="\
        Data capture rate (frames per second). All data is captured in sync.")
    parser.add_argument('--save_rate', type=float, default=1, help="\
        Data save rate (frames per second). MUST be less than or equal to capture_rate.")
    parser.add_argument('--capture_temp', type=bool, default=True, help="\
        Enable / disable capturing of temperature data \
        from cameras during test.")
    parser.add_argument('--save_images', type=bool, default=True, help="\
        Enable / disable saving of images during. \
        Image will still be grabbed from camera but \
        will not be saved to file.")
    parser.add_argument('--left_serial', type=str, default="", help="\
        Camera serial number for left camera. \
        If not specified will connect to first two \
        basler cameras found connected.")
    parser.add_argument('--right_serial', type=str, default="", help="\
        Camera serial number for right camera. \
        If not specified will connect to first two \
        basler cameras found connected.")
    parser.add_argument('--virtual', type=bool, default=False, help="\
        Enable camera emulation. Useful for testing. \
        Cameras are expected with serials '0815-0000' & '0815-0001'")
    args = parser.parse_args()
    # Check arguments are valid
    # If one camera serial is given then both must be given
    left_serial_given = args.left_serial != ""
    right_serial_given = args.right_serial != ""
    if left_serial_given and not right_serial_given:
        err_msg = "left_serial given without right_serial. \
            Both left and right MUST be given if specifing camera serials."
        raise Exception(err_msg)
    if right_serial_given and not left_serial_given:
        err_msg = "right_serial given without left_serial. \
            Both left and right MUST be given if specifing camera serials."
        raise Exception(err_msg)
    # Check output path exists
    if not os.path.exists(args.output):
        err_msg = "Output path does not exist: " + args.output
        raise Exception(err_msg)
    # Save rate must be less than or equal to capture rate
    if args.save_rate > args.capture_rate:
        raise Exception("Save rate must be less than or equal to capture rate")
    return args


def main() -> int:
    # Get command line arguments
    args = parse_args()
    TitaniaTest.enableCameraEmulation(args.virtual)
    # Check connected devices against arguments
    left_serial = None
    right_serial = None
    if args.left_serial != "":
        # If serials are specified then check they are connected
        TitaniaTest.checkSerialPairConnected(left_serial, right_serial)
        left_serial = args.left_serial
        right_serial = args.right_serial
    if args.left_serial == "":
        # If serials are not specifed then
        # check only two cameras are connected and get their serials
        left_serial, right_serial = TitaniaTest.getSerialPairConnected()
    if left_serial is None or right_serial is None:
        # This shouldn't be possible as previous error checking
        # should always set serials or raise an exception
        raise Exception("Failed to get valid camera serials")
    # Define test parameters
    test_params = TitaniaTest.TitaniaTestParams(
        left_serial=left_serial, right_serial=right_serial,
        output_folderpath=args.output,
        capture_rate=args.capture_rate,
        save_rate=args.save_rate,
        save_images=args.save_images,
        capture_temperature=args.capture_temp,
        virtual_camera=args.virtual,
    )
    TitaniaTest.validateTitaniaTestParams(test_params)
    # Run test
    exit_code = TitaniaTest.run(test_params)
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
