from pypylon import pylon

from pypylon import genicam
from pypylon import pylon
import sys

left_serial = "40098270"
right_serial = "40098281"

# Number of images to be grabbed.
countOfImagesToGrab = 10

maxCamerasToUse = 2

# The exit code of the sample application.
exitCode = 0

try:

    # Get the transport layer factory.
    tlFactory = pylon.TlFactory.GetInstance()

    # Get all attached devices and exit application if no device is found.
    devices = tlFactory.EnumerateDevices()
    if len(devices) == 0:
        raise pylon.RuntimeException("No camera present.")

    # Create an array of instant cameras for the found devices and avoid exceeding a maximum number of devices.
    cameras = pylon.InstantCameraArray(min(len(devices), maxCamerasToUse))

    l = cameras.GetSize()

    # Create and attach all Pylon Devices.
    for i, cam in enumerate(cameras):
        cam.Attach(tlFactory.CreateDevice(devices[i]))

        # Print the model name of the camera.
        print("Using device ", cam.GetDeviceInfo().GetModelName())

    # Starts grabbing for all cameras starting with index 0. The grabbing
    # is started for one camera after the other. That's why the images of all
    # cameras are not taken at the same time.
    # However, a hardware trigger setup can be used to cause all cameras to grab images synchronously.
    # According to their default configuration, the cameras are
    # set up for free-running continuous acquisition.
    cameras.StartGrabbing()

    while True:
        if not cameras.IsGrabbing():
            break

        grabResult = cameras.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        # When the cameras in the array are created the camera context value
        # is set to the index of the camera in the array.
        # The camera context is a user settable value.
        # This value is attached to each grab result and can be used
        # to determine the camera that produced the grab result.
        cameraContextValue = grabResult.GetCameraContext()

        # Print the index and the model name of the camera.
        print("Camera ", cameraContextValue, ": ", cameras[cameraContextValue].GetDeviceInfo().GetModelName())
        
        # Now, the image data can be processed.
        print("GrabSucceeded: ", grabResult.GrabSucceeded())
        img = grabResult.GetArray()

        # Get temporature
        temp = cameras[cameraContextValue].DeviceTemperature.GetValue()
        print("Temp: ", temp)


except genicam.GenericException as e:
    # Error handling
    print("An exception occurred.", e)
    exitCode = 1

# Comment the following two lines to disable waiting on exit.
sys.exit(exitCode)