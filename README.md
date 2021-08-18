# Titania Testing
Tests to run on Titania cameras to monitor performance over time.  
These tests include the following:
 - Thermal monitoring of internal camera temperatures
 - Image data capture
 - Logging of test results

## Run
To test a Titania system, plug the camera USB into a USB 3.0 port on your machine.  
Then run the test with the python test script:
```
python run.py --titania_serial <serial number>
```
### Options
The following options are available on the command line to setup the type of test that will be run on the device. Each option is available as a command line parameter and should be run with the following format:
```
python run.py --option variable
```

| Option         | Type    | Description                                                                                                                            | Default |
|----------------|---------|----------------------------------------------------------------------------------------------------------------------------------------|---------|
| output         | string  | Folderpath to store test results. Test data includes log file of results and any images captured during the test.                      | "."     |
| capture_fps    | float   | Data capture rate (frames per second). All data is captured in sync.                                                                   |  1      |
| save_fps       | float   | Data save rate (frames per second). MUST be less than or equal to capture_fps.                                                         |  1      |
| disable_temp   | bool    | Disable capturing of temperature data from cameras during test.                                                                        | False   |
| disable_images | bool    | Disable saving of images during. Image will still be grabbed from camera but will not be saved to file.                                | False   |
| titania_serial | string  | Titania unique serial number. Found printed on the back of Titania. Specify this or directly specify left and right serials. If no serials are specified will connected to the first two basler cameras found connected. | ""      |
| left_serial    | string  | camera serial number for left camera. If no serials are specified will connected to the first two basler cameras found connected.      | ""      |
| right_serial   | string  | camera serial number for right camera. If no serials are specified will connected to the first two basler cameras found connected.     | ""      |
| virtual        | bool    | Enable camera emulation. Useful for internal testing. Cameras are expected with serials '0815-0000' & '0815-0001'                      | False   |

Boolean options are False if omitted and True if provided. e.g.
```
python run.py --disable_temp
```
Will disable capturing temperature data during test.

### Results
Each test will log will capture data at the capture rate specified and send the data to a log file. The name of this file will be generated using the unix timestamp and the left and right serial numbers of the camera used (e.g. TT_1629119898_40081086_40081087.txt). The format of this file is a comma seperated text file with the following information: 
| Time | Left image filename | Right image filename | Left temperature | Right temperature | Left grab success | Right grab success |
|------|---------------------|----------------------|------------------|-------------------|-------------------|--------------------|
|      |                     |                      |                  |                   |                   |                    |

An example of the contents a file with this format is shown below:
```
time,left_img,right_img,left_temp,right_temp,left_success,right_success
1629119898,1629119898_l.png,1629119898_r.png,60.22,60.32,1,1
1629120151,1629120151_l.png,1629120151_r.png,60.23,60.31,1,1
```

Turning off capture_temp or capture_image will result in the same data format but columns will not be populated. For example the following is a file where image saving was disabled:
```
time,left_img,right_img,left_temp,right_temp,left_success,right_success
1629119898,,,60.22,60.32,1,1
1629120151,,,60.23,60.31,1,1
```

If images are saved as part of the test then these will be saved in the same folder as the log file, named using the unix timestamp and '_l' for left camera and '_r' for right camera (e.g. '1629119898_l.png')

## Future Work
 - Phase SDK support