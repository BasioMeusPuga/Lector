# Modified from: http://drumcoder.co.uk/blog/2010/nov/16/python-code-generate-svg-pie-chart/

import os
import math

class GeneratePie():
    def __init__(self, progress_percent, temp_dir=None):
        self.progress_percent = int(progress_percent)
        self.temp_dir = temp_dir

    def generate(self):
        lSlices = (self.progress_percent, 100 - self.progress_percent)  # percentages to show in pie

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
            lSvgPath += "<path d='%s' style='stroke:#c579be; fill:url(#%s);'/>" % (
                lPath, lGradient)
            lIndex += 1

        lSvg = """
        <svg  xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
        <defs>
            <radialGradient id="myRadialGradientGreen" r="65%%" cx="0" cy="0" spreadMethod="pad">
            <stop offset="0%%"   stop-color="#c579be" stop-opacity="1"/>
            <stop offset="100%%" stop-color="#c579be" stop-opacity="1" />
            </radialGradient>
        </defs>
        <defs>
            <radialGradient id="myRadialGradientOrange" r="65%%" cx="0" cy="0" spreadMethod="pad">
            <stop offset="0%%"   stop-color="#6c4268" stop-opacity="1"/>
            <stop offset="100%%" stop-color="#6c4268" stop-opacity="1" />
            </radialGradient>
        </defs>

        %s
        <!--  <circle cx="%d" cy="%d" r="100" style="stroke:#6c4268; fill:none;"/> -->
        </svg>
        """ % (lSvgPath, lOffsetX, lOffsetY)


        if self.temp_dir:
            svg_path = os.path.join(self.temp_dir, 'lector_progress.svg')
            lFile = open(svg_path, 'w')
            lFile.write(lSvg)
            lFile.close()
        else:
            return lSvg
