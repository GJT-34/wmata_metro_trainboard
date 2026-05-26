# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2023-03-12

- Added a new font ('Metroesque.bdf') that is designed to be similar to the Metro PIDS font
- Added the number of cars in each train to the display
- Added the ability to catch more networking errors (including the dreaded "Timed out waiting for SPI char" error) and trigger an automatic reloading of _code.py_ if repeated attempts to restart the data flow are unsuccessful
- Added functionality to address single-tracking
- Added functionality to correct for inconsistencies and excessively long names in the 'Destination' reported by WMATA API (e.g., 'NewCrltn' can also be reported as 'N Carrollton' or 'NEW CARROLLTON')
- Note: The additions do not include changes from the [Scottie Garcia fork](https://github.com/scottiegarcia/dc-metro) (i.e., multiple station support, walk time filtering, optional off hours configuration, and MetroHero API Support)
- Updated CircuitPython references to CircuitPython 8 in the README
- Updated list of Metro stations in the README to reflect changed names and additional Silver Line stations

## [1.0.1] - 2023-03-18

- Updated metro_api.py with additional corrections to standardize the 'Destination' reported by the WMATA API

## [2.0.0] - 2026-05-13

- Completely revised code with new functionality

## [2.1.0] - 2026-05-13

- Added Metrobus functionality
