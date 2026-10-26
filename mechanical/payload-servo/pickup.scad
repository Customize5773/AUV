// Two-jaw pickup concept, mm. Linkage/bearings/horn must follow the chosen servo.
ball_d = 40;
open = true;
pad_t = 2;
finger_t = 5;
finger_h = 30;
gap = open ? 52 : ball_d - 0.5; // Nominal pad compression; verify force on actual ball.
$fn = 64;
assert(ball_d >= 35 && ball_d <= 45);
color("steelblue") difference() {
    translate([-20,-38,20]) cube([40,76,5]);
    for (y=[-30,30]) translate([0,y,19]) cylinder(h=7,d=4.5);
}
for (side=[-1,1]) {
    color("orange") translate([-8, side*(gap/2+pad_t+finger_t/2)-finger_t/2,-5])
        cube([16,finger_t,finger_h]);
    color("gray") translate([-8,side*(gap/2+pad_t/2)-pad_t/2,-5])
        cube([16,pad_t,finger_h]);
}
if ($preview) color([1,1,1,.5]) sphere(d=ball_d);
