# ESPHome-Config

ESPHome configuration templates and projects.

## Release History

- Version 2.1:
  - Updated to use ESPHome's [CH390 ethernet controller][esphome-blog-ch390-link] after my [PR][esphome-pr-18226-link] landed.
  - Updated deprecated `rgb_order` to `channel_colors`.
  - Added ESPHome `min_version` to templates (required to use `CH390` and `channel_colors`).
- Version 2.0:
  - Refactored the layout to be fleet conformant.
  - Added Elecrow Thinknode M7 support.
  - Added CH390 ethernet controller support (ESPHome [PR][esphome-pr-18226-link] submitted).
  - Added Micro-Air EasyStart support.
  - Added Apollo's PLT-1B support.
  - Added Unexpected Maker ProS3D support.
  - Added SmartHomeShop CeilSense support.
  - Added Waveshare ESP32-S3-ETH support.
  - Added RGB LED status support for ethernet controllers.

<!-- External -->

[esphome-blog-ch390-link]: https://esphome.io/blog/2026/08/19/esphome-2026-8/#new-hardware-support
[esphome-pr-18226-link]: https://github.com/esphome/esphome/pull/18226
