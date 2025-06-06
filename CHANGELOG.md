# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Refactored project structure to follow domain-driven design principles
- Updated Docker configuration
- Improved Python package management with updated dependencies

### Added
- Added notion-client package to dependencies
- Added proper Python module path handling in Docker

## [0.1.1] - 9-1-2024

### Added 
- Multi server support. The capability to send Notion notifications to multiple servers based on the list of discord channel id's in constants.

## [0.1.0] - 29-12-2023

### Added
- load_start_time and save_start_time functions functions added to keep track of the bots start time. This handles instances where the bot may be restarted which would previously cause delays and potentially missed aggregate updates.
- This CHANGELOG file.

### Changed
- Frequency in which notion_aggregate_updates_notifications is called within bot.py

[unreleased]: https://github.com/BloomGameStudio/NotionDiscordIntegration/compare/staging...dev
[0.1.1]: https://github.com/BloomGameStudio/NotionDiscordIntegration/releases/tag/0.1.1
[0.1.0]: https://github.com/BloomGameStudio/NotionDiscordIntegration/releases/tag/0.1.0
