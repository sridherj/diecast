Goal:
/cast-refine-requirements was a good start, but over a period of time have found there are lot more things we can do to get much better output.

Few things I have in mind:
1. One of the key things is separating WHAT/HOW; Key focus of refine-requirements should be to get the WHAT right very quickly for the users; HOW sometimes is useful in certain types of goals, and sometimes its directional as well that may change based on the explorations we used (like Notes).
2. Diff users have diff types of workflows and we should be aware of that when creating the output
3. Create HTML output instead of md file? I am okay having md file as well if useful, but main goal is to have html output as it helps consume certain info much quicker than long md files. Also depending upon the nature of the goal, the html structure may change a bit. Detecting the intent of the user may be very helpful in finalizing the html format of the refined requirements file. 
4. Inline comments (or annotation based in UI like google docs) - are there standard libraries we can use? does it require us to move to react/nextjs?
5. Till the comments are resolved, we'll continue in refined-requirements creating v2, v3 version files. Old versions need not be in main folder - it can be moved to some archive folder or moved to db (think db may be better for older artifacts)?
6. Requirement files should be the source of truth. So if downstream (exploration, planning, execution) something changes around the requirements, I want these files to be updated to reflect it - eg: like new additions at the end - and the user should know it (notified that requirements changed, what changed, and where it came from). Requirements should never silently drift out of date relative to the work.

Notes:
- generally i have worked across diff kinds of projects in ~/workspace/second-brain, ~/workspace/linkedout-oss, ~/workspace/diecast. If you
  check diff requirements, writeup files you will have an idea of diff types of requirements/writeups. Goal for refined requirements should be 
  for the human to very quickly grasp what is being requested (with some ideas around how sometimes), or sometimes research etc. do you have 
  some good ideas on how to go about this? I want to evolve the cast-refine-requirements skill to produce great readable HTML file that one can
  quickly grasp. Illustrations, progressive disclosure, clear organization hierarchy like levels - L1/L2/L3.. and diff treatments to them 
  (color, size, design elements) 
- classify diff workflows based on user intent and we may have diff formats for them for output file organization; eg: Bug fix, Data Analysis, Debug, new small pilot feature, new initiative (big, needs clean architecture), prd creation, add tests, create POC, heavy ui flow (may require some ui mocks in the requirement file organized along user flows). It may be worthwhile to do some online research on what's the best way to represent each of them and even create some inspiration templates. It may be better to highlight this in the top of the document - eg: You are 'building a new feature' for XYZ, You are trying to 'analyze past historical data' -- something like that or like a standard list of pills as this may have a very diff workflow from here. The entire UI may change to adapt to this work.
- cast-preso* skills have some useful ideas here for presentation and tips/tricks on how it leverages diff ui elements for better communication. remember its primarily for presentation, but we can get inspiration.
- any improvements to refine-requirements from gbrain?
- Useful to spend a bit of time on diff types of workflows and start building the UI for some of the common flows.


