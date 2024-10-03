
reload = """
function reloadLast() {
    /*
    let lastPage = getCookie("lastPage");
    console.log('reloadLast: lastPage:', lastPage);
    let currentPage = window.location.pathname;
    console.log('reloadLast: currentPage:', currentPage);
    let lastModifiedDate = document.lastModified;
    console.log("Last Modified:" + lastModifiedDate);
    if (!lastPage || (lastPage !== currentPage)) {
        setCookie("lastPage", currentPage, 7);  // Set new cookie
        setCookie("eventSelection", '', 7);  // Set new cookie
        setCookie("lastBib", '', 7);  // Set new cookie
        return;
    }
    */

    let eventSelectionStr = getCookie("eventSelection");
    let waveSelectionStr = getCookie("waveSelection");
    let lastBib = getCookie("lastBib");
    let bibHighlighted = getCookie("bibHighlighted");

    if (eventSelectionStr === "") { return; }

    var eventSelection = JSON.parse(eventSelectionStr);
    if (eventSelection === null) { return; }
    TET(eventSelection);  // Restore last selected table if same page

    if (lastBib !== "") { 
        highlightBibNumber(lastBib, 'yellow', true); 
        lastBibNumber = lastBib;
        document.getElementById("bibInput").value = lastBib;
    }
    if (bibHighlighted !== "") {
        bigHighlighted = JSON.parse(bibHighlighted);
        console.log('reloadLast: bigHighlighted:', bigHighlighted);
        bigHighlighted.forEach(function(bib) {
            highlightBibNumber(bib, 'beige', true, true);
        });
    }
    if (waveSelectionStr === "") { return; }
    var waveSelection = JSON.parse(waveSelectionStr);
    if (waveSelection === null) { return; }
    TWT(waveSelection);  // Restore last selected table if same page
}

window.onload = reloadLast;


"""
