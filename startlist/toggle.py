toggle = """
/* Reset the selection cell background color and hide the info and wave tables */
function resetSelection(selectionStr) {
    console.log('setSelection:', selectionStr);
    if (selectionStr === null) { return; }

    var selection = JSON.parse(selectionStr);
    console.log('setSelection:', selection);
    let [eventInfoCellId, infoTableId, waveTableAllId] = selection;
    console.log('resetSelection ID:', eventInfoCellId);
    console.log('resetSelection ID:', infoTableId);
    console.log('resetSelection ID:', waveTableAllId);
    clearBackgroundColor(eventInfoCellId);
    setDisplayInvisible(infoTableId);
    setDisplayInvisible(waveTableAllId);
}

/* Set the selection cell background color and show the info and wave tables */
function setSelection(selectionStr) {
    console.log('setSelection:', selectionStr);
    if (selectionStr === null) { return; }

    var selection = JSON.parse(selectionStr);
    console.log('setSelection:', selection);
    let [eventInfoCellId, infoTableId, waveTableAllId] = selection;
    console.log('setSelection Cell ID:', eventInfoCellId);
    console.log('setSelection Info ID:', infoTableId);
    console.log('setSelection Wave ID:', waveTableAllId);
    setBackgroundColor(eventInfoCellId, 'yellow');
    setDisplayVisible(infoTableId);
    setDisplayVisible(waveTableAllId);
}

var lastEventSelectionStr = null;
var lastWaveSelectionStr = null;

function toggleEventTable(toggleList ) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('toggleEventTable:', toggleList);
    newEventSelectionStr = toggleTableInternal(toggleList, lastEventSelectionStr);
    console.log('toggleEventTable: XXXX newEventSelectionStr:', newEventSelectionStr);
    if (newEventSelectionStr === null || newEventSelectionStr === '') { return; }

    resetSelection(lastEventSelectionStr);
    resetSelection(lastWaveSelectionStr);

    setSelection(newEventSelectionStr);
    lastEventSelectionStr = newEventSelectionStr;
    setCookie("eventSelection", lastEventSelectionStr, 7);  // Set new cookie

    waveSelection = [null, null, toggleList[2]];
    toggleWaveTable(waveSelection);
    lastWaveSelectionStr = JSON.stringify(waveSelection);
}

function toggleWaveTable(toggleList) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('toggleWaveTable:', toggleList);
    lastWaveSelectionStr = toggleTableInternal(toggleList, lastWaveSelectionStr);
    console.log('toggleWaveTable: lastWaveSelectionStr:', lastWaveSelectionStr);
    if (lastWaveSelectionStr === null || lastWaveSelectionStr === '') { return; }
    resetSelection(lastWaveSelectionStr);
    setSelection(lastWaveSelectionStr);
    lastWaveSelectionStr = lastWaveSelectionStr;
    setCookie("waveSelection", lastWaveSelectionStr, 7);  // Set new cookie
}

function toggleTableInternal(toggleList, lastSelectionStr ) {

    console.log('toggleTableInternal: toggleList:', toggleList);
    let [eventInfoCellId, infoTableId, waveTableAllId] = toggleList;
    console.log('toggleTable ID:', eventInfoCellId);
    console.log('toggleTable ID:', infoTableId);
    console.log('toggleTable ID:', waveTableAllId);

    let currentSelectionStr = JSON.stringify(toggleList);
    console.log('toggleTableInternal: current selection str:', currentSelectionStr);

    if (lastSelectionStr !== null && lastSelectionStr !== currentSelectionStr) {
        console.log('toggleEventTable: reset last selection:', lastSelectionStr);
        resetSelection(lastSelectionStr);
        lastSelectionStr = null;
    }
    return currentSelectionStr;
}
"""
