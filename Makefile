# Build the dashboard.
#
# Using the default values, the dashboard will be available at:
#     build/dashboard.html

python := /usr/bin/python
ifneq ("$(wildcard .venv)", "")
	# Use python from virtualenv (if available)
	python := .venv/bin/python
endif
pythonflags :=
dir_build := build
dir_src := dashboard


.PHONY: all
all:  $(dir_build)/dashboard.html


.PHONY: clean
clean:
	rm -rf $(dir_build)


# Build dashboard
$(dir_build)/%.html:  $(dir_src)/%.py $(dir_src)/%.js  |  $(dir_build)
	$(python) $(pythonflags) $<
	mv $(<:.py=.html) $@
	cp $(<:.py=.js) $(dir $@)


# Create build directory
$(dir_build):
	mkdir $@
