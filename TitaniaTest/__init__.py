import sys
import os
import time
import random
from typing import NamedTuple
from pypylon import pylon, genicam
import cv2


class TitaniaTestParams(NamedTuple):
    left_serial: str
    right_serial: str
    output_folderpath: str
    capture_rate: float
    save_rate: float
    save_images: bool
    capture_temperature: bool
    virtual_camera: bool


def validateTitaniaTestParams(test_params: TitaniaTestParams) -> bool:
    # Check valid camera serial
    if test_params.left_serial == "" and test_params.right_serial == "":
        raise Exception("Camera serial empty")
    # Check output path exists
    if not os.path.exists(test_params.output_folderpath):
        err_msg = "Output path does not exist: " + \
            test_params.output_folderpath
        raise Exception(err_msg)
    # Save rate must be less than or equal to capture rate
    if test_params.save_rate > test_params.capture_rate:
        raise Exception("Save rate must be less than or equal to capture rate")


def enableCameraEmulation(enable):
    if enable:
        os.environ["PYLON_CAMEMU"] = "2"
    else:
        os.environ["PYLON_CAMEMU"] = "0"


def checkSerialPairConnected(left_serial: str, right_serial: str) -> bool:
    camera_serials = getCameraSerials()
    # Check they are connected
    if left_serial not in camera_serials:
        raise Exception("Left camera not found: " + left_serial)
    if right_serial not in camera_serials:
        raise Exception("Right camera not found: " + right_serial)
    return True


def getSerialPairConnected() -> list:
    camera_serials = getCameraSerials()
    # Check only two cameras are connected and get their serials
    if len(camera_serials) > 2:
        raise Exception("Too many camera connected. \
            Please specify --left_serial and --right_serial.")
    if len(camera_serials) < 2:
        raise Exception("Not enough camera connected. Found " +
                        str(len(camera_serials)) + " cameras.")
    left_serial = camera_serials[0]
    right_serial = camera_serials[1]

    return left_serial, right_serial


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
        cameras = pylon.InstantCameraArray(len(devices))

        # Create and attach all Pylon Devices.
        for i, cam in enumerate(cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))

            # Print the serial of the camera.
            cam_serial = cam.GetDeviceInfo().GetSerialNumber()
            print("Serial: ", cam_serial)
            serial_list.append(cam_serial)

        return serial_list

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred.", e)
        return []


def getLogFileName() -> str:
    # Get current unix time
    unix_time = str(int(time.time()))
    # Create file name from unix time
    log_file_name = "TT_" + unix_time + ".txt"
    return log_file_name


def run(test_params: TitaniaTestParams) -> int:
    exit_code = 0
    # Generate names for filepaths
    log_filename = getLogFileName()
    log_filepath = os.path.join(test_params.output_folderpath, log_filename)

    try:
        # Get the transport layer factory.
        tlFactory = pylon.TlFactory.GetInstance()

        # Get all attached devices and exit application if no device is found.
        devices = tlFactory.EnumerateDevices()
        if len(devices) < 2:
            raise pylon.RuntimeException(
                "Missing cameras. Requires at least 2 cameras are connected.")

        # Create an array of instant cameras
        available_cameras = pylon.InstantCameraArray(len(devices))
        cameras = pylon.InstantCameraArray(2)
        cameras_found = [False, False]

        # Create and attach Pylon Devices.
        # Attach to camera serials from params
        # Left camera assigned to index 0, right camera to index 1
        for i, cam in enumerate(available_cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))

            # Print the serial of the camera.
            cam_serial = cam.GetDeviceInfo().GetSerialNumber()
            if (cam_serial == test_params.left_serial):
                cameras[0].Attach(tlFactory.CreateDevice(devices[i]))
                cameras_found[0] = True
            if (cam_serial == test_params.right_serial):
                cameras[1].Attach(tlFactory.CreateDevice(devices[i]))
                cameras_found[1] = True

        if False in cameras_found:
            error_msg = "Failed to find specified camera serials \
                on connected devices."
            raise Exception(error_msg)

        # Start capture
        cameras.StartGrabbing(
            pylon.GrabStrategy_LatestImageOnly,
            pylon.GrabLoop_ProvidedByUser)

        # Set capture rate
        for i, cam in enumerate(cameras):
            if test_params.virtual_camera:
                cam.AcquisitionFrameRateAbs.SetValue(test_params.capture_rate)
            else:
                cam.AcquisitionFrameRate.SetValue(test_params.capture_rate)
            cam.AcquisitionFrameRateEnable.SetValue(True)

        # Write log file header line
        header_msg = \
            "time,left_img,right_img,left_temp,right_temp," \
            + "left_success,right_success\n"
        f = open(log_filepath, "w")
        f.write(header_msg)
        f.close()

        # Calculate save rate (in ms)
        save_rate = test_params.save_rate
        last_save_time = time.time()

        while True:
            # Get capture time
            capture_time = time.time()
            capture_time = "{:10.4F}".format(capture_time)
            # Define default values for log data
            left_temp = ""
            right_temp = ""
            left_image_filename = ""
            right_image_filename = ""
            left_success = "0"
            right_success = "0"

            save_this_frame = False

            # Check cameras are grabbing
            if cameras.IsGrabbing():
                # Read camera data
                grabResult_left = cameras[0].RetrieveResult(
                    20000, pylon.TimeoutHandling_ThrowException)
                grabResult_right = cameras[1].RetrieveResult(
                    20000, pylon.TimeoutHandling_ThrowException)

                time_since_save = time.time() - last_save_time
                if time_since_save > save_rate:
                    save_this_frame = True
                    last_save_time = time.time()

                if save_this_frame:
                    # Save camera images to file
                    if grabResult_left.GrabSucceeded():
                        left_success = "1"
                        if test_params.save_images:
                            img = grabResult_left.GetArray()
                            left_image_filename = capture_time + "_l.png"
                            left_image_filepath = os.path.join(
                                test_params.output_folderpath,
                                left_image_filename)
                            cv2.imwrite(left_image_filepath, img)
                    if grabResult_right.GrabSucceeded():
                        right_success = "1"
                        if test_params.save_images:
                            img = grabResult_right.GetArray()
                            right_image_filename = capture_time + "_r.png"
                            right_image_filepath = os.path.join(
                                test_params.output_folderpath,
                                right_image_filename)
                            cv2.imwrite(right_image_filepath, img)

                    if test_params.capture_temperature:
                        # Get temperature
                        if test_params.virtual_camera:
                            # generate fake temperature values
                            left_temp_data = random.uniform(30, 60)
                            right_temp_data = random.uniform(30, 60)
                        else:
                            # read temperature from cameras
                            left_temp_data = \
                                cameras[0].DeviceTemperature.GetValue()
                            right_temp_data = \
                                cameras[1].DeviceTemperature.GetValue()
                        left_temp = "{:.3F}".format(left_temp_data)
                        right_temp = "{:.3F}".format(right_temp_data)

            if save_this_frame:
                # Define log message
                # time,left_img,right_img,left_temp,right_temp,left_success,right_success
                log_msg = capture_time \
                    + "," + left_image_filename + "," + right_image_filename \
                    + "," + left_temp + "," + right_temp \
                    + "," + left_success + "," + right_success \
                    + "\n"

                # Append log message line to file
                f = open(log_filepath, "a")
                f.write(log_msg)
                f.close()

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred.", e)
        exit_code = 1

    return exit_code


# Entry point used to debug Titania Test
def main() -> int:
    # Choose params
    virtual_cams = True
    left_serial = ""
    right_serial = ""
    output_folderpath = "."
    capture_rate = 1.0
    save_rate = 1.0
    save_images = True
    capture_temp = True

    enableCameraEmulation(virtual_cams)
    # Check connected devices against arguments
    if left_serial != "":
        # If serials are specified then check they are connected
        checkSerialPairConnected(left_serial, right_serial)
    if left_serial == "":
        # If serials are not specifed then
        # check only two cameras are connected and get their serials
        left_serial, right_serial = getSerialPairConnected()
    if left_serial is None or right_serial is None:
        # This shouldn't be possible as previous error checking
        # should always set serials or raise an exception
        raise Exception("Failed to get valid camera serials")
    # Define test parameters
    test_params = TitaniaTestParams(
        left_serial=left_serial, right_serial=right_serial,
        output_folderpath=output_folderpath,
        capture_rate=capture_rate,
        save_rate=save_rate,
        save_images=save_images,
        capture_temperature=capture_temp,
        virtual_camera=virtual_cams
    )
    validateTitaniaTestParams(test_params)
    # Run test
    exit_code = run(test_params)
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
