# StabiliKnee
AI-powered knee brace that detects dangerous motion 30ms before dislocation and automatically tightens to prevent injury.

## Inspiration:
A common issue that our teammate faced was easily dislocating the knee and typical knee braces only provide passive support which is not stable enough to prevent dislocations. So we decided to take matters into our own hands and create this system that can provide active tension to the knee in order to prevent these dislocations. 
## What It Does
- Detects dangerous knee rotation using ITG-3200 gyroscope
- Monitors knee flexion via flex sensor  
- Triggers servo-actuated brace tightening when risk threshold exceeded
- Provides ~30ms predictive response window
  
## How we built it:
We used an arduino Uno R3, a breadboard, IMU, and a flex bend sensor to detect abnormalites in an individuals knee movements. The IMU uses the 3-axis gyroscope to detect rotations and if a rotation that would cause a dislocation was to take place then we would increase the risk factor. The other end of the risk factor comes from the flex bend sensor and when that bends to a certain range then the risk factor would increase again. We are looking for a risk threshold and when this is achieved the servo motor turns on to create a tension to immobilize the joint of the dislocation and support the knee. We coded it using the arduino IDE and arduino C++.

## Hardware
- Arduino Uno R3
- ITG-3200 3-axis gyroscope (ATAVRSBIN1)
- Flex sensor (A0)
- SG90 servo
- 10kΩ resistor


## Challenges:
Our first biggest challenge was connecting the IMU because we did not have the original board that it was supposed to connect to so we had to look into the board and IMU specifications to reverse engineer the ports and determine which ones we would need to use and where. 
Our next challenge came with working this IMU. Since it is a 15 year old device we had a lot of issues in regards to the pointer addresses that the system outputted. We eventually solved it through documentation, videos, and testing algorithms. 

## Accomplishments:
Our biggest accomplishment is getting the IMU working and also getting the servo to react so quickly. This is important because dislocations can happen in an instant and having a quick tension applied would reduce the chance of a dislocation significantly. 

## Whats next for StabiliKnee:
One of our biggest issues right now is that we only had one 9V battery to power the device however with all of the sensors and motors we are using this is not enough to power it therefore we need to keep a computer attached for constant power. We also need to make it more compact, one way we plan to do this is to reduce the size of the breadboard we use which is an easy fix however we did not have access to a smaller one to do this. 

