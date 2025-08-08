```
         ___                      _   _  __        _           _
        / __|_ _ ___ _  _ _ _  __| | | |/ /___ _ _| |_ _ _ ___| |
       | (_ | '_/ _ \ || | ' \/ _` | | ' </ _ \ ' \  _| '_/ _ \ |
        \___|_| \___/\_,_|_||_\__,_| |_|\_\___/_||_\__|_| \___/_|
████████╗ █████╗ ██████╗ ██╗     ██╗███████╗████████╗███████╗██████╗       ▄
╚══██╔══╝██╔══██╗██╔══██╗██║     ██║██╔════╝╚══██╔══╝██╔════╝██╔══██╗      █
   ██║   ███████║██████╔╝██║     ██║███████╗   ██║   █████╗  ██████╔╝      █
   ██║   ██╔══██║██╔═══╝ ██║     ██║╚════██║   ██║   ██╔══╝  ██╔══██╗     ███
   ██║   ██║  ██║██║     ███████╗██║███████║   ██║   ███████╗██║  ██║  █▄█████▄█
   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝  █▀  █  ▀█
 ▪ Proudly vibe-coded by Bill Eckerson with ChatGPT, 2025.

░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░
```
This trinity of web tools operates the digital signage tap lists at Ground Kontrol Classic Arcade in Portland, OR. The three parts are as follows:  

**`red-side.html/blue-side.html`**:  
These are the actual tap list displays for each side of the bar.  
**`red-side-editor.html/blue-side-editor.html`**:  
These tools provide bartenders/managers with the ability to switch which beers are currently being displayed, as well as mark taps as sold out.  
**`beer-db-editor.html`**:  
This tool allows managers to add/remove/modify beers to/from/within the "database."  

<h1 style="color: #fabd2f;">Taplists</h1>  

The taplist itself is basically fully autonomous and shouldn't ever really need to be directly modified or manipulated by employees. The Raspberry Pi on which the tap list is displayed is simply configured to point to a single web page, and that is `red-side.html` on the red side and `blue-side.html` on the blue side.  
Everything from theming to the scaling of the text and images is handled automatically through javascript and should Just Work™. Changes to the tap list on either side are made through the *Taplist Editors*.
<h1 style="color: #fabd2f;">Taplist Editors</h1>  

The Taplist Editors are the primary pages bartenders/managers/promotions will be dealing with to modify the live tap lists. Again, this is `red-side-editor.html` on red side and `blue-side-editor.html` on the blue side. These pages will ideally be bookmarked on each side's iPad and can be quickly pulled up to swap a keg to another beer, or mark a tap as temporarily sold out. There is no need to do anything on the tap list's end (for example, a refresh or reboot). Each tap list has a "refresh token" that is checked every 10 seconds, and when the ![Static Badge](https://img.shields.io/badge/💾_save_changes-00faff?style=flat) button is clicked, a new refresh token is generated that tells the tap list to refresh itself.  

### About the `red-beers.json` and `blue-beers.json` files: ###  
The `red-beers.json` and `blue-beers.json` files, again, shouldn't really ever need to be modified or manipulated by employees, but for demystification purposes let's go over the format of the files a bit.  
Example data in `blue-beers.json:`
```
  "theme": "blue side",
  "refreshToken": "feslv48btx6",
  "beers": [
    {
      "id": "y6cfdc6z",
      "soldOut": false
    },
```
The first piece of information tells the taplist which CSS style (or theme) to apply. In red-beers.json, this obviously reads `"theme": "red side",`. The second piece of information is the aforementioned refreshToken, which is randomly generated, and the tap lists check for changes to this token every 10 seconds. When the taps are modified or marked as sold out, a new token is written, the tap list recognizes this change, and refreshes the page. Next is the list of beers for each side. There will be 8 entries on blue side and 12 entries on red side. The only two pieces of data required are the "BeerID" (see Beer Database Editor section), which tells the taplist which beer's information to load (brewery name, abv, city/state, logo, etc). The only other piece of information is the "soldOut" flag, which tells the tap list whether a beer is available or not, which bartenders can change by selecting "SOLD OUT" on the Taplist Editor.  

If you are switching a keg/tap to a beer that does not already exist in the Taplist Editor, that is when you move to the *Beer Database Editor*. 
<h1 style="color: #fabd2f;">Database Editor</h1>

When the Beer DB Editor is launched, initially two options are presented. The ![Static Badge](https://img.shields.io/badge/💾_backup_database-blue?style=flat) button simply creates a copy of the existing `beer-database.json` in the /json folder with the time and date appended to the filename (e.g. `beer-database-backup-20250729-220947.json`). It's probably a good idea to click this before making any changes. The **(choose a beer...)** dropdown contains all editing tools.  

## Menu options:
- ### 🍻 = show all beers =  
  - This option displays all beers currently in the `beer-database.json` in a single table. This allows for quick changes to data, or removal of listings by clicking the [X] in the delete column. When you've finished editing, click ![Static Badge](https://img.shields.io/badge/save_all-green?style=flat) at the bottom of the screen. A **"Saved!"** message will appear at the top of the screen if successful.  

- ### 🍺 = add new beer =  
  - This option displays a blank "beer card," in which the new beer's data can be entered. ABV should be in the format `x.x`, where x is a single digit number. No trailing percent sign is required. State should be a two-letter abbreviation. The **= select logo =** dropdown will display a list of every brewery logo in /logos. Once you've chosen all your data, click ![Static Badge](https://img.shields.io/badge/save-544e68?style=flat). Clicking ![Static Badge](https://img.shields.io/badge/cancel-333333?style=flat) returns you to the main screen.
  
- ### **selecting a single beer**  
  - Alternatively, you can select a single beer from the dropdown to edit its details in the "card" view. The ![Static Badge](https://img.shields.io/badge/delete-d08159?style=flat) button removes the beer from the database. 
---  

### A note about brewery logos:
Creating new brewery logos is outside the scope of this particular document, but they must be in SVG format, a single layer whose ID is "logo-face," and the fill color must be *unset* so that the javascript theming engine can write this value. I may at some point create a tool that aids in the logo creation process.  
In the meantime, here is a full video demonstration on logo creation:  
![Static Badge](https://img.shields.io/badge/YouTube_→-red?style=flat&logo=youtube) **[GK Taplister: How to Create New Brewery Logo Files](https://www.youtube.com/watch?v=B-KgX5yj-r8)**
### How the beer-database.json is formatted:  
A single entry:
```
{
  "id": "0fbc3j77",
  "brewery": "2 towns",
  "title": "brightcider",
  "city": "corvallis",
  "state": "or",
  "style": "hard apple cider",
  "abv": "6.0",
  "logoPath": "2towns.svg"
},
```
The `id` field is the beer's "beerID." This is randomly generated and assigned to a beer on creation. The other fields should be pretty self-explanatory.


--- 
<details>
<summary>Release Notes</summary>

## [Taplist & Editor]
- **v1.0 07.14.2025:**
  - Full working tap list and editor.
  - Editor reads inline beer JSON array and user can edit fields and save a new index.html.

- **v1.1 07.15.2025:**
  - Moved styles, all SVG and JSONs to external files from inline HTML.
  - Created master beer-database.json where we can add new beers.
  - Created new editor that uses dropdown menus instead of text fields and writes to
beers.json live with PHP (and therefore removed JSON editing instructions from this document).
  - Added ability to mark taps as sold out.

- **v1.2 07.16.2025:**
  - Various bugs squashed, some light code cleanup.
  - Added theming and ability for end-user to choose themes from taplist_editor.html. Five basic themes
to start: "hyper," "pinku," "lemon-lime," "evening pastel," "vania." Waiting on hardware for deployment.

- **v1.3 07.18.2025:**
  - Added entire new  layer between starfield and HTML called "battle." On this layer, the GK ship
"mascot" flies by in one of three states: "normal," in which it just zooms by the screen, "broken," it
which it slowly drifts by while spinning like a derelict satellite, and "combat," in which a Galaga
alien sprite flies by and the GK ship follows, shooting at it.

- **v1.4 07.20.2025:**
  - Duplicated taplist and taplist editor into red and blue sides, edited all necessary logic including PHP calls and JSON organization etc in order to have two separate taplists that share resources but have independent formatting and saving.
  - Removed theming engine per owner request, but left code in, only commented out. If anybody in the future wants to re-implement the theming you can uncomment the the marked lines in the editor files to restore the theme control. Themes can be added/modified with the structure in styles.css. I left it all in, just in case.
  - Fixed a bug in the spaceship spawning that prevented it from spawning from the left or top sides of the screen.

## [DB Editor]
- **v.1 07.24.25**
  - Core functionality working. Utility pulls beers from JSON, shows them in table. Can edit, add, remove beers.

- **v.12 07.25.25**
  - Added "card" system for individual beers. Selecting a single beer from the dropdown displays a "card" with fields for beer info plus a logo preview for editing single beers.

- **v.13 07.25.25**
  - "Add beer" function creates blank card that user can fill out.
  - Additional format tweaks to card system.

- **v.25 07.26.25**
  - Format tweaks. 
  - Added database backup function that creates copy of taplist with date and timestamp appended to file name.
  - Added working status messages at top of screen ("Saved!" "Error saving..." "Database backed up, etc").

- **v.3 07.27.25**
  - Added "tapper" save animation.
  - Switched from frame to time-based timing. Animation scaled 2X.
  - Additional layout tweaks.

- **v.35 07.28.25**
  - Formatted "show all" table.
  - Realized I may need to add a "beer ID" field to JSON to avoid sorting and indexing confusion. Might require rewrites of sections of all three parts.
  - Began calling project "Taplister" and treating all three components as a single entity.

## Taplister
- **v1.0 07.30.25**
  - Switched the way JSONs were formatted and read from indexes to "beer ID" system, where each beer is given a unique 8 character identifier. Changed all logic to work with this new format.
  - Moved all JSON, PHP, and CSS into their own folders because root directory was getting cluttered. Will continue to tweak but considering this deployable.  

  Todo:  
  - Limit state field to two characters
  - Add motion to tap list logo?
</details>
