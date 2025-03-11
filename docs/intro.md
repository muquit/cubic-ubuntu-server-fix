# Introduction

This document describes a bug in [Cubic Issues](https://github.com/PJ-Singh-001/Cubic/issues/381) that prevents proper extraction of Ubuntu Server ISOs and the solution we implemented. The issue occurs because Ubuntu Server ISOs have a two-part squashfs structure consisting of a base file (`ubuntu-server-minimal.squashfs`) and a secondary overlay file (`ubuntu-server-minimal.ubuntu-server.squashfs`). Cubic was only successfully extracting the first file and failing on the second, resulting in a non-functional ISO missing important components like WiFi drivers.

