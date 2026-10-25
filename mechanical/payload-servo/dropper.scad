// Concept only: millimetres, one ball; measure servo and fabricate/test before use.
ball_d = 45;       // Rulebook payload maximum diameter; design for the largest ball.
clearance = 3;     // Diametral allowance, must be checked after printing.
wall = 3;
height = 58;
plate_t = 3;
pivot_x = 40;
open_angle = 0;    // 0 closed, 120 open; CAD angle is not a calibrated PWM command.
$fn = 96;
bore = ball_d + clearance;
assert(bore > ball_d && height > ball_d);
// Tube remains fixed; two mounting ears receive M4 clearance holes.
color("steelblue") difference() {
    union() {
        translate([0,0,2]) cylinder(h=height,d=bore+2*wall);
        for (y=[-35,35]) translate([-12,y-7,8]) cube([24,14,6]);
    }
    translate([0,0,1]) cylinder(h=height+2,d=bore);
    for (y=[-35,35]) translate([0,y,7]) cylinder(h=8,d=4.5);
}
// Rotating shelf, shaft parallel to tube axis. Bracket/shaft bearings are not modeled.
color("orange") translate([pivot_x,0,0]) rotate([0,0,open_angle])
    translate([-pivot_x,0,-plate_t]) difference() {
        hull() {
            translate([-31,-31,0]) cube([62,62,plate_t]);
            translate([pivot_x,0,0]) cylinder(h=plate_t,d=16);
        }
        translate([pivot_x,0,-1]) cylinder(h=plate_t+2,d=4.5);
    }
// Display ball, excluded from fabricated geometry when preview is disabled.
if ($preview) color([1,1,1,.5]) translate([0,0,ball_d/2]) sphere(d=ball_d);
