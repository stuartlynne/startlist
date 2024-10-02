notes = """
var notesDictionary = {};  // Dictionary to store notes keyed by bib number

//var lastBibNumber = null;
function openNoteBib(bibNumber, setFlag, debug = false) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('highlightBibNumber:', bibNumber, highlightColor, setFlag);
    var found = false;
    var allTables = document.querySelectorAll('table[id*="_wave_"]');
    foundFlag = false;
    allTables.forEach(function(table) {
        console.log('searchBibNumber: table:', table.id);
        var rows = table.getElementsByTagName('tr');
        for (var i = 1; i < rows.length; i++) {  // Skip header row
            index = (table.id.endsWith('_wave_all')) ? 1 : 0; 
            var bibCell = rows[i].getElementsByTagName('td')[index];  // Assuming Bib is in the first column
            if (!bibCell || !bibCell.innerText || bibCell.innerText === "") { continue; }
            if (debug) {
                console.log('searchBibNumber: innerText:', bibCell.innerText);
            }
            if (bibCell.innerText === bibNumber) {
                console.log('searchBibNumber: %s found table: %s row: %d id: %s XXX', bibNumber, table.id, i, rows[i].id);
                foundFlag = true;
                rows[i].querySelectorAll('td').forEach(function(td) {
                    if (!setFlag) { setFlag = td.style.backgroundColor === 'white'; }
                    td.style.backgroundColor = setFlag ? highlightColor : 'white';
                });
            }
        }
    });
    console.log('searchBibNumber: foundFlag:', foundFlag);
    return foundFlag;
}

let xbigHighlighted = [];
function xtoggleBib(bibId) {
    toggleNoteRow(bibId);
    console.log('toggleBib:', bib);

    var allTables = document.querySelectorAll('table[id*="_wave_"]');
    foundFlag = false;
    allTables.forEach(function(table) {
        console.log('searchNoteNumber: table:', table.id);

    })

    if (bib) {
        if (bigHighlighted.includes(bib)) {
            bigHighlighted = bigHighlighted.filter(item => item !== bib);
            highlightBibNumber(bib, 'beige', false, true);
        } else {
            bigHighlighted.push(bib);
            highlightBibNumber(bib, 'beige', true, true);
        }
        setCookie("bibHighlighted", JSON.stringify(bigHighlighted), 7);  // Set new cookie
    }
}


// Toggle visibility of the note row
function toggleNoteRow(bib) {
    console.log('toggleNoteRow:', bib);
    return;
    var noteRow = document.getElementById(bib);
    if (noteRow.style.display === 'none') {
        noteRow.style.display = 'table-row';
    } else {
        noteRow.style.display = 'none';
    }
}

// Handle keypress event
function handleNoteKeyPress(event, bib) {
    if (event.key === 'Enter') {
        saveNoteData(bib);  // Save the note when Enter is pressed
    }
}

// Handle keydown event (you can extend this if needed)
function handleNoteKeyDown(event, bib) {
    // Optional: Additional handling on key down
}

// Save the note data when the input field loses focus or Enter is pressed
function saveNoteData(bib) {
    var noteInput = document.querySelector(`#note-${bib} input`);
    if (noteInput) {
        notesDictionary[bib] = noteInput.value;
        console.log(`Saved note for bib ${bib}: ${noteInput.value}`);
    }
}


"""
