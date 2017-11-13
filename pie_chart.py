# Modified from: http://drumcoder.co.uk/blog/2010/nov/16/python-code-generate-svg-pie-chart/

import math

class GeneratePie():
    def __init__(self, progress_percent):
        self.progress_percent = int(progress_percent)

    def generate(self):
        lSlices = (100 - self.progress_percent, self.progress_percent)  # percentages to show in pie

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
            lSvgPath += "<path d='%s' style='stroke:#2c2c2c; fill:url(#%s);'/>" % (
                lPath, lGradient)
            lIndex += 1

        lSvg = """
        <svg  xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink">
        <defs>
            <radialGradient id="myRadialGradientGreen" r="65%%" cx="0" cy="0" spreadMethod="pad">
            <stop offset="0%%"   stop-color="#2c2c2c" stop-opacity="1"/>
            <stop offset="100%%" stop-color="#2c2c2c" stop-opacity="1" />
            </radialGradient>
        </defs>
        <defs>
            <radialGradient id="myRadialGradientOrange" r="65%%" cx="0" cy="0" spreadMethod="pad">
            <stop offset="0%%"   stop-color="#4caf50" stop-opacity="1"/>
            <stop offset="100%%" stop-color="#4caf50" stop-opacity="1" />
            </radialGradient>
        </defs>

        %s
        <!--  <circle cx="%d" cy="%d" r="100" style="stroke:#4caf50; fill:none;"/> -->
        </svg>
        """ % (lSvgPath, lOffsetX, lOffsetY)

        return lSvg
