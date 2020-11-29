// NanoVNA Control Panel
// Bruce MacKinnon KC1FSZ

function setupTabNavigation(tabs) {
    $(tabs).focus(function(event) {
        $(this).find("[role='tablist']").find("[aria-selected='true']").focus();
    })
    $(tabs).find("[role='tab']").click(function(event) {
        var selectedEl = $(this).closest("[role='tablist']").find("[aria-selected='true']")
        // Unselect the current tab
        $(selectedEl).attr("aria-selected", "false")
        // Remove from tab rotation
        $(selectedEl).attr("tabindex", "-1")
        // Select the new tab
        $(this).attr("aria-selected", "true")
        // Add into tab rotation so that when someone back-tabs out of 
        // the tabpanel then end up on the selected tab control.
        $(this).attr("tabindex", "0")
        // Give focus
        $(this).focus()
        return false
    })
    $(tabs).find("[role='tab']").keydown(function(event) {
        if (event.which == 37 || event.which == 39) {
            var selectedEl = $(this).closest("[role='tablist']").find("[aria-selected='true']")
            // Unselect the current tab
            $(selectedEl).attr("aria-selected", "false")
            // Remove from tab rotation
            $(selectedEl).attr("tabindex", "-1")
            // Right arrow
            if (event.which == 39) {
                // Is there a next sibling? If so focus, if not wrap to the first
                if ($(selectedEl).next().length != 0) {
                    targetEl = $(selectedEl).next()
                } else {
                    targetEl = $(this).closest("[role='tablist']").children().first()
                }
            }
            // Left arrow 
            else {
                // Is there a previous sibling?  If so focus, if not wrap to the lset
                if ($(selectedEl).prev().length != 0) {
                    targetEl = $(selectedEl).prev()
                } else {
                    targetEl = $(this).closest("[role='tablist']").children().last()
                }
            }
            // Select the new tab
            $(targetEl).attr("aria-selected", "true")
            // Add into tab rotation so that when someone back-tabs out of 
            // the tabpanel then end up on the selected tab control.
            $(targetEl).attr("tabindex", "0")
            $(targetEl).focus()
            return false
        } else if (event.which == 9) {
            // Search up to find the parent tabs
            var tabsDiv = $(this).closest(".tabs")
            controlsId = $(this).attr("aria-controls")
            $(tabsDiv).find("#" + controlsId).focus()
            return false
        } else {
            return true;
        }
    });
    // This event handler is to control which tab panel is visible
    // when moving between tab controls.
    $(tabs).find("[role='tab']").focus(function(event) {
        controlsId = $(this).attr("aria-controls")
        // Search up
        var tabsDiv = $(this).closest(".tabs")
        // Hide all
        $(tabsDiv).find("[role=tabpanel]").hide()
        // Show the selection
        $(tabsDiv).find("#" + controlsId).show()
    });
}

function do_sweep(panel) {

    // Get the form inputs
    var params = {
        cal_preset: $(panel).find("#s14").val(),
        start_frequency_mhz: $(panel).find("#s11").val(),
        end_frequency_mhz: $(panel).find("#s12").val(),
        step_frequency_mhz: $(panel).find("#s13").val()
    }

    // Load up the sweep table user server-side data
    $.get("/api/sweep", params)
        .done(function(data) {
            if (data.error) {
                $(panel).find(".result-div").html("<p role='alert'>" + data.message + "</p>")
            } else {
                $(panel).find(".result-div").html(template_0(data))
            }
        });
}
