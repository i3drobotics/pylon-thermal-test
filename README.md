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
python run.py
```
### Options
The following options are available on the command line to setup the type of test that will be run on the device. Each option is available as a command line parameter and should be run with the following format:
```
python run.py --option variable
```
| Option        | Type    | Description                                                                                                                            | Default |
|---------------|---------|----------------------------------------------------------------------------------------------------------------------------------------|---------|
| output        | string  | Folderpath to store test results. Test data includes log file of results and any images captured during the test.                      | "."     |
| rate          | integer | Data capture rate (frames per second). All data is captured in sync.                                                                   |  1      |
| capture_temp  | bool    | Enable / disable capturing of temperature data from cameras during test.                                                               | true    |
| save_images | bool    | Enable / disable saving of images during. Image will still be grabbed from camera but will not be saved to file.                                                                                    | true    |
| left_serial   | string  | camera serial number for left camera. If not specified will connect to first two basler cameras found connected.                       | ""      |
| right_serial  | string  | camera serial number for right camera. If not specified will connect to first two basler cameras found connected.                      | ""      |

### Results
Each test will log will capture data at the capture rate specified and send the data to a log file. The name of this file will be generated using the unix timestamp and the left and right serial numbers of the camera used (e.g. TT_1629119898_40081086_40081087.txt). The format of this file is a comma seperated text file with the following information: 
| Time | Left image filename | Right image filename | Left temperature | Right temperature | Left grab success | Right grab success |
|------|---------------------|----------------------|------------------|-------------------|-------------------|--------------------|
|      |                     |                      |                  |                   |                   |                    |

An example of the contents a file with this format is shown below:
```
time,left_img,right_img,left_temp,right_temp,left_success,right_success
1629119898,1629119898_l.png,1629119898_r.png,60.22,60.32,Success,Success
1629120151,1629120151_l.png,1629120151_r.png,60.23,60.31,Success,Success
```

Turning off capture_temp or capture_image will result in the same data format but columns will not be populated. For example the following is a file where image saving was disabled:
```
time,left_img,right_img,left_temp,right_temp,left_success,right_success
1629119898,,,60.22,60.32,Success,Success
1629120151,,,60.23,60.31,Success,Success
```

If images are saved as part of the test then these will be saved in the same folder as the log file, named using the unix timestamp and '_l' for left camera and '_r' for right camera (e.g. '1629119898_l.png')

## Future Work
 - Phase SDK support