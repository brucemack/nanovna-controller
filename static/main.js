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

// This function is used for implementing a multi-step workflow.  Each step
// has its own <div> that is shown in sequence.
function showStepDiv(divSet, step, prepareFunction) {
    // Hide all steps
    $(divSet).find(".step-div").hide()
    // Show the step that was selected
    $(divSet).find(".step-div").eq(step).show()
    // Focus the right control for this step
    $(divSet).find(".step-div").eq(step).find(".step-focus").focus()
    // Call prepare
    if (prepareFunction != null) {
        prepareFunction($(divSet).find(".step-div").eq(step), step)
    }
}

function do_sweep(panel) {

    // Get the form inputs
    var params = {
        cal_preset: $(panel).find(".s4").val(),
        start_frequency_mhz: $(panel).find(".s1").val(),
        end_frequency_mhz: $(panel).find(".s2").val(),
        step_frequency_mhz: $(panel).find(".s3").val(),
        one_row: "true"
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

function do_complex_sweep(panel) {

    // Get the form inputs
    var params = {
        cal_preset: $(panel).find(".s4").val(),
        start_frequency_mhz: $(panel).find(".s1").val(),
        end_frequency_mhz: $(panel).find(".s2").val(),
        step_frequency_mhz: $(panel).find(".s3").val(),
        one_row: "false"
    }

    // Load up the sweep table user server-side data
    $.get("/api/sweep", params)
        .done(function(data) {
            if (data.error) {
                $(panel).find(".result-div").html("<p role='alert'>" + data.message + "</p>")
            } else {
                $(panel).find(".result-div").html(template_1(data))
            }
        });
}

/*
This function is used to validate the start/end frequency range that is
entered into the calibration form.  This makes sure that both values
have been entered and that the start is less than then end.

If a validation problem is detected then the workflow button is
marked to prevent progress to the next step.
*/
function validateCalibrationRange(panel) {

    startValue = $(panel).find(".s1").val().trim()
    endValue = $(panel).find(".s2").val().trim()

    try {
        if (startValue == "" || endValue == "") {
            throw "missing value"
        }
        var start = parseFloat(startValue)
        var end = parseFloat(endValue)
        if (isNaN(start) || isNaN(end) || end < start) {
            throw "range error"
        }
        // If we get to this point then the values are correct and we can
        // allow the workflow to proceed
        $(panel).find("#s30").text("Continue")
        $(panel).find("#s30").data("block-workflow", false)
    }
    catch (ex) {
        $(panel).find("#s30").text("Invalid Range")
        $(panel).find("#s30").data("block-workflow", true)
    }
}

// This function is called at the start of each calibration step to
// make any necessary adjustments to the step DIV.
function prepareCalStepDiv(stepDiv, stepNumber) {
    // On the first step we take a look at the status of the NanoVNA
    // and set the button text accordingly
    if (stepNumber == 0) {
        params = {
            step: 0
        }
        $.get("/api/calibrate", params)
        .done(function(data) {
            if (data == "OK") {
                $(stepDiv).find(".step-focus").text("Begin calibration")
            } else {
                $(stepDiv).find(".step-focus").text("NanoVNA is disconnected, please connect")
            }
        });
    }
}

// This function is called to perform a calibration step.  This is where
// we interact with the server/device.
function doCalStep(panel, step, successCb, errorCb) {

    var params;

    // STEP 0: Does nothing
    // STEP 3: Short
    // STEP 4: Open
    // STEP 5: Load
    // STEP 6: Repeat
    if (step == 0 || step == 3 || step == 4 || step == 5 || step == 6) {
        params = {
            step: step
        }
    }
    // STEP 1: Establishes preset
    else if (step == 1) {
        params = {
            step: step,
            cal_preset: $(panel).find(".s4").val()
        }
    }
    // STEP 2: Establishes range
    else if (step == 2) {
        params = {
            step: step,
            start_frequency_mhz: $(panel).find(".s1").val(),
            end_frequency_mhz: $(panel).find(".s2").val()
        }
    }

    $.get("/api/calibrate", params)
        .done(function(data) {
            if (data == "OK") {
                successCb()
            } else {
                errorCb()
            }
        });
}

function do_status_refresh(panel) {
    // Load up the sweep table user server-side data
    $.get("/api/status")
        .done(function(data) {
            if (data.error) {
                $(panel).find(".result-div").html("<p role='alert'>" + data.message + "</p>")
            } else {
                $(panel).find(".result-div").html(template_2(data))
            }
        });
}
