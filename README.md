# WMATA Metro Info Board

This project contains the source code to create your own customizable Washington Metropolitan Area Transit Authority (WMATA) Metro information board, showing both Metrorail and Metrobus information. It is written using CircuitPython targeting the [Adafruit Matrix Portal S3](https://www.adafruit.com/product/5778) and 64x32 RGB LED matrices, and it uses information that WMATA makes publicly available. Features include:
- Multiple options for displaying train and bus arrival predictions
- The ability to auto-rotate through multiple "screens," including multiple arrival prediction screens
- The ability to prioritize/filter the display of trains and buses that are predicted to arrive at a station or stop only after you can get there
- The ability to display rail alerts and elevator outages
- A font customized to resemble the font WMATA uses on its train boards

![bd1](img/bd1.jpg)
![bd2](img/bd2.jpg)
![bd3](img/bd3.jpg)

## Background

Metro's first generation of digital prediction arrival boards--which WMATA calls passenger information display system (PIDS) monitors--have been a familiar sight since their introduction at Metrorail stations in October 2000. They've been ubiquitous at Metro stations, typically with a couple at each track and sometimes at one or more at station entrances as well. Many millions of riders have seem them, given that Metro routinely has averaged over 100 million rides a year since these train boards were implemented. WMATA's use of digital information boards at bus stops came later, with the first displays installed in late 2008, but these too have slowly become more common.

The train and bus boards consist of LED panels with extremely limited pixel densities and color capabilities. The train boards have a resolution of 192x68 pixels spread out on a display that is over two feet in diagonal length. To put that into perspective, a typical phone these days will have a pixel density of 300 to over 500 pixels per inch (PPI). The train panels also show only red, green, and yellow colors. The bus boards sport similarly low-density pixel counts on a wide and narrow display that shows only a single color. WMATA has begun phasing out these train and bus boards in favor of next-gen displays, but the original boards still have some old-school charm, especially the train boards. 

In November 2020, a [project](https://github.com/metro-sign/dc-metro) landed on github that allowed people to make their own Metro train boards. The only hardware needed was a LED panel and a controller device called the Matrix Portal M4, which could be purchased together for around $65 on Adafruit, before shipping and taxes. The LED panel recommended for that project has a pixel resolution of just 64x32. That's not an exact match for what Metro's train boards, but it's similar. Anyone looking to implement this project also needed to obtain a free API key from WMATA. The project received some online attention, such as this DCist [article](https://dcist.com/story/23/03/16/heres-how-to-build-your-own-mini-metro-arrival-screen-for-your-home-or-office/). 

In 2023, I became one of several people who set up code forks on github of the original project, which has not been updated since 2020. At the time, my main contribution was to edit the default font to more closely resemble the font on Metro's train boards. This was tricky not only because of the space considerations of the 64x32 screen, but because Metro's train boards use multiple fonts with subtle differences. You can see some examples in these train board pics:

![font1_circles](img/font1_circles.jpg)
![font2_circles](img/font2_circles.jpg)

Since then, I've added several features to the code and have expanded it to provide information on Metrobus, leading to a change in hardware requirements for the project. The project that was released in 2020 called for the use of the Matrix Portal M4 to control the LED panel. Because the additional features use more memory than the original version, my version of the code is designed to run on the newer Matrix Portal S3. The S3 has far more memory than the M4, which is no longer for sale.

I've found this Metro information board to be a unusual but useful piece of kit to have, and maybe you will too.

## Prerequisites

### Hardware

- A [Matrix Portal S3](https://www.adafruit.com/product/5778). You can buy the S3 directly from Adafruit at the link above. I found mine at Micro Center. 
- A **64x32 RGB LED matrix** compatible with the _Matrix Portal_. The version in the pictures above is my 4mm panel.
    - [64x32 RGB LED Matrix - 3mm pitch](https://www.adafruit.com/product/2279)
    - [64x32 RGB LED Matrix - 4mm pitch](https://www.adafruit.com/product/2278)
    - [64x32 RGB LED Matrix - 5mm pitch](https://www.adafruit.com/product/2277)
    - [64x32 RGB LED Matrix - 6mm pitch](https://www.adafruit.com/product/2276)
- A **USB-C power supply**. 15w phone adapters (5V/3A) should work fine, while underpowered adapters can lead to Matrix Portal not running properly, or at all. The LED display uses a surprising amount of power.
- A **USB-C cable** that can connect your computer/power supply to the Matrix Portal. You'll be transferring some files to the Matrix Portal, so make sure it's a USB-C cable that handle data transfers, not just power delivery.
- A **3D printed case** that can hold the Matrix Portal and LED panel. This is optional, but it helps hide the wires behind the LED panel. I've had one for several years, but I don't recall where I got the design from.
- A [LED diffusion acrylic panel](https://www.adafruit.com/product/4594). This is also optional, but it helps tone down the lights on the LED panel. This is useful because the lights are much brighter (and better!) than the pictures suggest. 

### Tools
- A small phillips head screwdriver
- A hot glue gun _(optional)_
- Tape _(optional)_
- Zip ties _(optional)_

## Setup and Usage
- [Setting up the hardware](https://github.com/GJT-34/wmata_metro_train_board/blob/main/HARDWARE.md)
- [Installing the software](https://github.com/GJT-34/wmata_metro_train_board/blob/main/SOFTWARE.md)
- [Editing the configuration file](https://github.com/GJT-34/wmata_metro_train_board/blob/main/CONFIGURE.md)
- [Using the train board](https://github.com/GJT-34/wmata_metro_train_board/blob/main/USAGE.md)
