# Modified from: http://drumcoder.co.uk/blog/2010/nov/16/python-code-generate-svg-pie-chart/

import os
import math

from PyQt5 import QtGui


def generate_pie(progress_percent, temp_dir=None):
    progress_percent = int(progress_percent)

    lSlices = (progress_percent, 100 - progress_percent)  # percentages to show in pie

    lOffsetX = 150
    lOffsetY = 150

    lRadius = 100

    def endpoint(pAngleInRadians, pRadius, pCentreOffsetX, pCentreOffsetY):
        """
        Calculate position of point on circle given an angle, a radius,
        and the location of the center of the circle
        Zero line points west.
        """
        lCosAngle = math.cos(pAngleInRadians)
        lSinAngle = math.sin(pAngleInRadians)
        lStartLineDestinationX = pCentreOffsetX - (lRadius * lCosAngle)
        lStartLineDestinationY = pCentreOffsetY - (lRadius * lSinAngle)

        return (lStartLineDestinationX, lStartLineDestinationY)


    GRADIENTS = ('myRadialGradientGreen', 'myRadialGradientOrange',
                 'myRadialGradientGreen', 'myRadialGradientOrange')
    DEGREES_IN_CIRCLE = 360.0
    lSvgPath = ""
    lCurrentAngle = 0
    lTotalSlices = 0
    lIndex = 0
    lSvgPath = ""
    for x in lSlices:
        lTotalSlices += x

    for lSlice in lSlices:
        lLineOneX, lLineOneY = endpoint(lCurrentAngle, lRadius, lOffsetX, lOffsetY)
        lLineOne = "M%d,%d L%d,%d" % (lOffsetX, lOffsetY, lLineOneX, lLineOneY)

        lDegrees = (DEGREES_IN_CIRCLE / lTotalSlices) * lSlice
        lRadians = math.radians(lDegrees)
        lCurrentAngle += lRadians
        lLineTwoX, lLineTwoY = endpoint(lCurrentAngle, lRadius, lOffsetX, lOffsetY)

        lRoute = 0
        if lDegrees > 180:
            lRoute = 1
        lArc = "A%d,%d 0 %d,1 %d %d" % (
            lRadius, lRadius, lRoute, lLineTwoX, lLineTwoY)
        lLineTwo = "L%d,%d" % (lOffsetX, lOffsetY)

        lPath = "%s %s %s" % (lLineOne, lArc, lLineTwo)
        lGradient = GRADIENTS[lIndex]
        lSvgPath += "<path d='%s' style='stroke:#097b8c; fill:url(#%s);'/>" % (
            lPath, lGradient)
        lIndex += 1

    lSvg = """
    <svg  xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <radialGradient id="myRadialGradientGreen" r="65%%" cx="0" cy="0" spreadMethod="pad">
        <stop offset="0%%"   stop-color="#11e0ff" stop-opacity="1"/>
        <stop offset="100%%" stop-color="#11e0ff" stop-opacity="1" />
        </radialGradient>
    </defs>
    <defs>
        <radialGradient id="myRadialGradientOrange" r="65%%" cx="0" cy="0" spreadMethod="pad">
        <stop offset="0%%"   stop-color="#097b8c" stop-opacity="1"/>
        <stop offset="100%%" stop-color="#097b8c" stop-opacity="1" />
        </radialGradient>
    </defs>

    %s
    <!--  <circle cx="%d" cy="%d" r="100" style="stroke:#097b8c; fill:none;"/> -->
    </svg>
    """ % (lSvgPath, lOffsetX, lOffsetY)


    if temp_dir:
        svg_path = os.path.join(temp_dir, 'lector_progress.svg')
        lFile = open(svg_path, 'w')
        lFile.write(lSvg)
        lFile.close()
    else:
        return lSvg


def pixmapper(current_chapter, total_chapters, temp_dir, size):
    # A current_chapter of -1 implies the files does not exist
    # A chapter number == Total chapters implies the file is unread
    return_pixmap = None

    if current_chapter == -1:
        return_pixmap = QtGui.QIcon(':/images/error.svg').pixmap(size)
        return return_pixmap

    if current_chapter == total_chapters:
        return_pixmap = QtGui.QIcon(':/images/checkmark.svg').pixmap(size)
    else:

        # TODO
        # See if saving the svg to disk can be avoided
        # Shift to lines to track progress
        # Maybe make the alignment a little more uniform across emblems

        progress_percent = int(current_chapter * 100 / total_chapters)
        generate_pie(progress_percent, temp_dir)
        svg_path = os.path.join(temp_dir, 'lector_progress.svg')
        return_pixmap = QtGui.QIcon(svg_path).pixmap(size - 4)  ## The -4 looks more proportional

    return return_pixmap
