LEFT_SERIAL=40098266
RIGHT_SERIAL=40098271
LEFT_EXPOSURE=4000.0
RIGHT_EXPOSURE=4000.0
CAMERA_FPS=10

python run.py --left_serial $LEFT_SERIAL --right_serial $RIGHT_SERIAL \
    --left_exposure $LEFT_EXPOSURE --right_exposure $RIGHT_EXPOSURE \
    --capture_fps $CAMERA_FPS --save_fps 10 --enable_imu --timeout 30.0 --output "./out/startup"
python run.py --left_serial $LEFT_SERIAL --right_serial $RIGHT_SERIAL \
    --left_exposure $LEFT_EXPOSURE --right_exposure $RIGHT_EXPOSURE \
    --capture_fps $CAMERA_FPS --save_fps 0.1 --enable_imu --timeout 0.0 --output "./out/main"