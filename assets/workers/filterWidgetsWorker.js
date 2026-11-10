self.onmessage = function (event) {
    const { filter, widgetItems, lastParentId } = event.data;

    const showAll = filter.length === 0;

    const visibleIds = [];
    const hiddenIds = [];

    widgetItems.forEach((widget) => {
        const matchesFilter = showAll || (widget.dataTitle.toLowerCase().includes(filter) && widget.dataSearch == 'true');
        const belongsToLastParent = widget.classes.includes(`c_${lastParentId}`);

        if ((showAll && belongsToLastParent) || (!showAll && matchesFilter)) {
            visibleIds.push(widget.id); // Widget should be visible
        } else {
            hiddenIds.push(widget.id); // Widget should be hidden
        }
    });

    self.postMessage({ visibleIds, hiddenIds });
};