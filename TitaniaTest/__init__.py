import sys
import os
import time
import random
import datetime
import threading
from typing import NamedTuple
import keyboard
from pypylon import pylon, genicam
import cv2


class TitaniaTestParams(NamedTuple):
    left_serial: str
    right_serial: str
    output_folderpath: str
    capture_fps: float
    save_fps: float
    save_images: bool
    capture_temperature: bool
    virtual_camera: bool
    timeout: float


def getLeftRightSerialFromTitaniaSerial(titania_serial: str) -> str:
    # Get left and right camera serials from the given titania serial
    # the titania serial should exists in the cameras user defined name
    # in the following format:
    # 'I3DRTitania-XXXXXXXX_l' and 'I3DRTitania-XXXXXXXX_r'
    try:
        # Get the transport layer factory.
        tlFactory = pylon.TlFactory.GetInstance()

        # Get all attached devices and exit application if no device is found.
        devices = tlFactory.EnumerateDevices()
        if len(devices) < 2:
            raise pylon.RuntimeException(
                "Missing cameras. Requires at least 2 cameras are connected.")

        # Create an array of instant cameras
        left_serial = None
        right_serial = None

        # Create and attach Pylon Devices.
        for device in devices:
            # Get camera serials from user defined name
            camera_defined_id = device.GetUserDefinedName()
            if "I3DRTitania" in camera_defined_id:
                camera_defined_id_array = camera_defined_id.split("_")
                if len(camera_defined_id_array) != 3:
                    err_msg = "Invalid device user id name format: " \
                        + camera_defined_id + " Expected the format: \
                        'I3DRTitania-XXXXXXXX_l'"
                    raise Exception(err_msg)
                cam_titania_serial = camera_defined_id_array[1]
                if cam_titania_serial == titania_serial:
                    if "l" in camera_defined_id:
                        left_serial = device.GetSerialNumber()
                    elif "r" in camera_defined_id:
                        right_serial = device.GetSerialNumber()

        if left_serial is None or right_serial is None:
            error_msg = "Failed to find valid camera serials \
                on connected devices."
            raise Exception(error_msg)

        return left_serial, right_serial

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred when getting camera serials.", e)
        return {}


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
    if test_params.save_fps > test_params.capture_fps:
        raise Exception("Save FPS must be less than or equal to capture FPS")


def enableCameraEmulation(enable: bool):
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

        # Create and attach all Pylon Devices.
        for device in devices:

            # Print the serial of the camera.
            cam_serial = device.GetSerialNumber()
            serial_list.append(cam_serial)

        return serial_list

    except genicam.GenericException as e:
        # Error handling
        print("An exception occurred when getting camera serials.", e)
        return []


def getLogFileName() -> str:
    # Get current time
    time_now = datetime.datetime.now()
    timestamp = time_now.strftime('%Y-%m-%d_%H_%M_%S_%f')
    # Create file name from unix time
    log_file_name = "TitaniaTest_" + timestamp + ".txt"
    return log_file_name


def run(test_params: TitaniaTestParams) -> int:

    exit_code = 0
    # Generate names for filepaths
    log_filename = getLogFileName()
    log_filepath = os.path.join(test_params.output_folderpath, log_filename)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    print("Test started: ", timestamp)

    try:
        # Get the transport layer factory.
        tlFactory = pylon.TlFactory.GetInstance()

        # Get all attached devices and exit application if no device is found.
        devices = tlFactory.EnumerateDevices()
        if len(devices) < 2:
            raise pylon.RuntimeException(
                "Missing cameras. Requires at least 2 cameras are connected.")

        # Create an array of instant cameras
        cameras = pylon.InstantCameraArray(2)
        cameras_found = [False, False]

        # Create and attach Pylon Devices.
        # Attach to camera serials from params
        # Left camera assigned to index 0, right camera to index 1
        for device in devices:
            # Print the serial of the camera.
            cam_serial = device.GetSerialNumber()
            if (cam_serial == test_params.left_serial):
                cameras[0].Attach(tlFactory.CreateDevice(device))
                cameras_found[0] = True
            if (cam_serial == test_params.right_serial):
                cameras[1].Attach(tlFactory.CreateDevice(device))
                cameras_found[1] = True

        if False in cameras_found:
            error_msg = "Failed to find specified camera serials \
                on connected devices."
            raise Exception(error_msg)

        # Start capture
        cameras.StartGrabbing(
            pylon.GrabStrategy_LatestImageOnly)

        # Set capture rate
        for cam in cameras:
            if test_params.virtual_camera:
                cam.AcquisitionFrameRateAbs.SetValue(test_params.capture_fps)
            else:
                cam.AcquisitionFrameRate.SetValue(test_params.capture_fps)
            cam.AcquisitionFrameRateEnable.SetValue(True)

        # Flip left camera images
        if not test_params.virtual_camera:
            cameras[0].ReverseX.SetValue(True)
            cameras[0].ReverseY.SetValue(True)

        # Write log file header line
        header_msg = \
            "time,left_img,right_img,left_temp,right_temp," \
            + "left_success,right_success\n"
        f = open(log_filepath, "w")
        f.write(header_msg)
        f.close()

        # Calculate save rate (in seconds)
        save_rate = 1.0 / test_params.save_fps
        last_save_time = time.time()

    except genicam.GenericException as e:
        # Error handling
        print("Camera exception occurred during test setup: ", e)
        exit_code = 1
        return exit_code

    try:
        start_time = time.time()
        while True:
            if test_params.timeout > 0:
                test_duration = time.time() - start_time
                if test_duration > test_params.timeout:
                    exit_code = 0
                    return exit_code

            # Get capture time
            time_now = datetime.datetime.now()
            # Convert to excel datetime serial
            excel_time = time_now.strftime('%Y-%m-%d %H:%M:%S.%f')
            image_tag_time = time_now.strftime('%Y-%m-%d_%H_%M_%S_%f')

            # Define default values for log data
            left_temp = ""
            right_temp = ""
            left_image_filename = ""
            right_image_filename = ""
            left_success = "0"
            right_success = "0"

            save_this_frame = False

            grabbing = cameras.IsGrabbing()

            # Check cameras are grabbing
            if grabbing:
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
                            left_image_filename = image_tag_time + "_l.png"
                            left_image_filepath = os.path.join(
                                test_params.output_folderpath,
                                left_image_filename)
                            cv2.imwrite(left_image_filepath, img)
                    if grabResult_right.GrabSucceeded():
                        right_success = "1"
                        if test_params.save_images:
                            img = grabResult_right.GetArray()
                            right_image_filename = image_tag_time + "_r.png"
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
                log_msg = excel_time \
                    + "," + left_image_filename + "," + right_image_filename \
                    + "," + left_temp + "," + right_temp \
                    + "," + left_success + "," + right_success \
                    + "\n"
                print(log_msg)

                # Append log message line to file
                f = open(log_filepath, "a")
                f.write(log_msg)
                f.close()

            if keyboard.is_pressed("q"):
                print("Test stopped")
                break

    except KeyboardInterrupt:
        # Error handling
        print("Test stopped.")
        exit_code = 0
        return exit_code
    except genicam.GenericException as e:
        # Error handling
        print("Camera exception occurred during test: ", e)
        exit_code = 1
        return exit_code


# Entry point used to debug Titania Test
def main() -> int:
    # Choose params
    virtual_cams = True
    left_serial = ""
    right_serial = ""
    output_folderpath = "."
    capture_fps = 10.0
    save_fps = 10.0
    timeout = 0.0  # zero = no timeout
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
        capture_fps=capture_fps,
        save_fps=save_fps,
        save_images=save_images,
        capture_temperature=capture_temp,
        virtual_camera=virtual_cams,
        timeout=timeout
    )
    validateTitaniaTestParams(test_params)
    # Run test
    exit_code = run(test_params)
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
