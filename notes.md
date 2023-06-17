# Fact Table

Index value
Website
The time of day
The surf spot (other table will provide information about surf spot)
The surf height
The rating
The wind speed
The primary swell (other swells will be in the swell table)
Tide
Water temp
Wetsuit recommendation
Next high tide
Next low tide
Daily blurb about surf (Actual blurb will be in other table)

# Goal

- Take a photo of a break
- Get the past 24 hours of data leading up till the photo
- Get the current conditions at the time of the photo

## What does this get us?

1. A database of photos and their associated conditions at the time and in the lead up (ie how those conditions came about)
2. If conditions look good, some data to help us predict when they could be good again
3. Overtime we may get photos of different breaks with similar conditions, which could help us determine which break we should go to based on the conditions
4. Build a collection of photos of breaks that don't have a surf report and see how they look in different conditions of nearby breaks.

## What data do we need

1. Photos
2. Swell data
3. Wind data
4. Bathymetry of break (dunno if even possible, especially beach breaks)
5. Tide data
6. Less important but the Surfline (and other sites) rating of the surf at the time
    - This could be used to help train models or provide an objective value to how good the conditions were
