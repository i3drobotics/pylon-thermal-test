import argparse
import sys
import os
import time
from typing import NamedTuple
from pypylon import pylon, genicam
import cv2


class TitaniaTestParams(NamedTuple):
    left_serial: str
    right_serial: str
    output_folderpath: str
    capture_rate: float
    save_images: bool
    capture_temperature: bool


def parse_args() -> argparse.Namespace:
    # parse command line argument
    parser = argparse.ArgumentParser(description="Titania Testing")
    parser.add_argument('--output', type=str, default=".", help="\
        Folderpath to store test results. \n \
        Test data includes log file of results and \
        any images captured during the test.")
    parser.add_argument('--rate', type=float, default=1, help="\
        Data capture rate (frames per second). All data is captured in sync.")
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
    return args


def getCameraSerials() -> list:
    # Get camera serials of currently connected basler devices
    serial_list = []
    try:
        # Get the transport layer factory.
        tlFactory = pylon.TlFactory.GetInstance()

        # Get all attached devices and exit application if no device is found.
        devices = tlFactory.EnumerateDevices()
        if len(devices) == 0:
            return []

        # Create an array of instant cameras for the found devices
        # and avoid exceeding a maximum number of devices.
        cameras = pylon.InstantCameraArray(min(len(devices)))

        # Create and attach all Pylon Devices.
        for i, cam in enumerate(cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))

            # Print the model name of the camera.
            cam_serial = cam.GetDeviceInfo().GetSerialNumber()
            print("Serial: ", cam_serial)
            serial_list.append(cam_serial)

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred.", e)
        return []


def getLogFileName() -> str:
    # Get current unix time
    unix_time = str(time.time())
    # Create file name from unix time
    log_file_name = "TT_" + unix_time + ".txt"
    return log_file_name


def run_test(test_params: TitaniaTestParams) -> int:
    exit_code = 0
    # Generate names for filepaths
    log_filename = getLogFileName()
    log_filepath = os.path.join(test_params.output_folderpath, log_filename)

    try:
        # Get the transport layer factory.
        tlFactory = pylon.TlFactory.GetInstance()

        # Get all attached devices and exit application if no device is found.
        devices = tlFactory.EnumerateDevices()
        if len(devices) == 0:
            raise pylon.RuntimeException("No camera present.")

        # Create an array of instant cameras
        cameras = pylon.InstantCameraArray(min(len(devices), 2))

        # Create and attach Pylon Devices.
        # TODO attach to camera serials from params
        # TODO left camera must be in index 0, right camera must be in index 1
        for i, cam in enumerate(cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))

            # Print the model name of the camera.
            print("Using device ", cam.GetDeviceInfo().GetModelName())

        # Start capture
        cameras.StartGrabbing(
            pylon.GrabStrategy_LatestImageOnly,
            pylon.GrabLoop_ProvidedByUser)

        # Set capture rate
        for i, cam in enumerate(cameras):
            acquisition_frame_rate = 1.0 / test_params.capture_rate
            cam.AcquisitionFrameRate.SetValue(acquisition_frame_rate)
            cam.AcquisitionFrameRateEnable.SetValue(True)

        while True:
            # Get capture time
            capture_time = str(time.time())
            # Define default values for log data
            left_temp = ""
            right_temp = ""
            left_image_filename = ""
            right_image_filename = ""
            left_success = "Failed"
            right_success = "Failed"
            # Check cameras are grabbing
            if cameras.IsGrabbing():
                # Read camera data
                grabResult_left = cameras[0].RetrieveResult(
                    20000, pylon.TimeoutHandling_ThrowException)
                grabResult_right = cameras[1].RetrieveResult(
                    20000, pylon.TimeoutHandling_ThrowException)

                # Check data capture success
                grabSuccess_left = \
                    grabResult_left.GetStatus() == pylon.GrabStatus_Success
                grabSuccess_right = \
                    grabResult_right.GetStatus() == pylon.GrabStatus_Success
                # Save camera images to file
                if grabSuccess_left:
                    left_success = "Success"
                    if test_params.save_images:
                        img = grabSuccess_left.GetArray()
                        left_image_filename = capture_time + "_l.png"
                        left_image_filepath = os.path.join(
                            test_params.output_folderpath,
                            left_image_filename)
                        cv2.imwrite(left_image_filepath, img)
                if grabSuccess_right:
                    right_success = "Success"
                    if test_params.save_images:
                        img = grabSuccess_right.GetArray()
                        right_image_filename = capture_time + "_r.png"
                        right_image_filepath = os.path.join(
                            test_params.output_folderpath,
                            right_image_filename)
                        cv2.imwrite(right_image_filepath, img)

                if test_params.capture_temperature:
                    # Get temperature
                    left_temp_data = cameras[0].DeviceTemperature.GetValue()
                    right_temp_data = cameras[1].DeviceTemperature.GetValue()
                    left_temp = str(left_temp_data)
                    right_temp = str(right_temp_data)

            # Define log message
            # time,left_img,right_img,left_temp,right_temp,left_success,right_success
            log_msg = capture_time \
                + "," + left_image_filename + "," + right_image_filename + \
                + "," + left_temp + "," + right_temp + \
                + "," + left_success + "," + right_success + \
                "\n"

            # Write log message to file
            f = open(log_filepath, "a")
            f.write(log_msg)
            f.close()

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred.", e)
        exit_code = 1

    return exit_code


def main() -> int:
    exit_code = 0
    # Get command line arguments
    args = parse_args()
    # Get currently connected devices
    camera_serials = getCameraSerials()
    # Check connected devices against arguments
    left_serial = None
    right_serial = None
    if args["left_serial"] != "":
        if args["left_serial"] not in camera_serials:
            raise Exception("Left camera not found: " + args["left_serial"])
        if args["right_serial"] not in camera_serials:
            raise Exception("Right camera not found: " + args["right_serial"])
        left_serial = args["left_serial"]
        right_serial = args["right_serial"]
    if args["left_serial"] == "":
        if len(camera_serials) > 2:
            raise Exception("Too many camera connected. \
                Please specify --left_serial and --right_serial.")
        if len(camera_serials) < 2:
            raise Exception("Not enough camera connected. Found " +
                            str(len(camera_serials)) + " cameras.")
        left_serial = camera_serials[0]
        right_serial = camera_serials[1]
    if left_serial is None or right_serial is None:
        # This shouldn't be possible as previous error checking
        # should always set serials or raise an exception
        raise Exception("Failed to get valid camera serials")
    # Define test parameters
    test_params = TitaniaTestParams(
        left_serial=left_serial, right_serial=right_serial,
        output_folderpath=args["output"],
        capture_rate=args["rate"],
        capture_images=args["capture_image"],
        capture_temperature=args["capture_temp"]
    )
    # Run test
    exit_code = run_test(test_params)
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
