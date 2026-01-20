# Chinese Word Hunt - Game Design Document

## Overview
A Chinese character puzzle game inspired by iMessage Word Hunt. Players swipe across adjacent radical tiles to form valid Chinese characters.

## Core Mechanics

### Grid
- 4×4 grid of radical tiles (16 tiles total)
- Each tile displays one of the 214 Kangxi radicals

### Gameplay
- Swipe across **adjacent tiles** (including diagonals) to select radicals
- Selected radicals are matched against the character database
- Valid characters are scored based on complexity
- Each character can only be found once per game

### Minimum Radical Count
- **2 radicals minimum** required to form a valid character
- Characters composed of 2-7 radicals are supported

### Scoring
- **Complexity-based scoring**: Points = sum of stroke counts of all component radicals
- Example: 休 (人 + 木) = 2 strokes + 4 strokes = **6 points**
- More complex characters with more/harder radicals score higher

### Board Generation
- **Hybrid approach**: Frequency-weighted + guaranteed solvable
- Common radicals (一, 口, 人, 木, 水, etc.) appear more frequently
- Board guarantees **~80 valid characters** can be formed via adjacent paths
- Ensures engaging gameplay with many discoverable solutions

### Adjacency Rules
- Tiles are adjacent horizontally, vertically, and diagonally
- Each tile can only be used once per character
- Path must be continuous (each new tile adjacent to the previous)

```
Grid positions and adjacency:
 0  1  2  3
 4  5  6  7
 8  9 10 11
12 13 14 15

Tile 5 is adjacent to: 0, 1, 2, 4, 6, 8, 9, 10
```

## Radical Reference
The game uses the 214 Kangxi radicals (康熙部首), the traditional system for categorizing Chinese characters established in the 18th-century Kangxi Dictionary.

## Data Source
Character decomposition data derived from CJKVI-IDS database (based on CHISE IDS Database), containing ~17,000 characters mapped to their component radicals.
