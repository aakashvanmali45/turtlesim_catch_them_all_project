#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from my_robot_interfaces.msg import Turtle
from my_robot_interfaces.msg import TurtleArray
from my_robot_interfaces.srv import CatchTurtle
from functools import partial

class TurtleControllerNode(Node): #change name
    def __init__(self):
        super().__init__("turtle_controller") #change
        self.turtle_to_catch_: Turtle = None
        self.catch_turtle_client = self.create_client(CatchTurtle, "catch_turtle")
        self.pose_: Pose = None
        self.alive_turtle_subscriber_ = self.create_subscription(TurtleArray, "alive_turtles", 
                                                                 self.callback_alive_turtles, 10)
        self.cmd_vel_publisher_ = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.pose_subscriber_ = self.create_subscription(Pose, "/turtle1/pose", 
                                                         self.callback_pose, 10)
        
        self.control_loop_timer_ = self.create_timer(0.01, self.control_loop)

    def callback_alive_turtles(self, turtle_list: TurtleArray):
        if len(turtle_list.turtles)>0:
            self.turtle_to_catch_ = turtle_list.turtles[0]
        

    def callback_pose(self, pose: Pose):
        self.pose_ = pose

    def control_loop(self):
        if self.pose_ == None or self.turtle_to_catch_ == None:
            return
        dist_x = self.turtle_to_catch_.x - self.pose_.x
        dist_y = self.turtle_to_catch_.y - self.pose_.y

        distance = math.sqrt(dist_x*dist_x + dist_y*dist_y)

        cmd = Twist()

        if distance > 0.5:
            cmd.linear.x = 2*distance
            
            goal_theta = math.atan2(dist_y, dist_x)
            diff = goal_theta - self.pose_.theta
            diff = (diff + math.pi) % (2 * math.pi) - math.pi
            cmd.angular.z = 6*diff

        else:

            cmd.linear.x = 0.0
            cmd.linear.z = 0.0
            self.call_catch_turtle_service(self.turtle_to_catch_.name)
            self.turtle_to_catch_=None


        self.cmd_vel_publisher_.publish(cmd)

    def call_catch_turtle_service(self, turtle_name):
        while not self.catch_turtle_client.wait_for_service(1.0):
            self.get_logger().warn("Wait for catch turtle serrvice..")

        request = CatchTurtle.Request()
        request.name = turtle_name

        future = self.catch_turtle_client.call_async(request)
        future.add_done_callback(partial(self.callback_call_catch_turtle, request=request))

    def callback_call_catch_turtle(self, future, request):
        response: CatchTurtle.Response = future.result()

        if not response.success:
            self.get_logger().error("Turtle "+ request.name+" couldnt be removed")

def main(args=None):
    rclpy.init(args=args)
    node = TurtleControllerNode() #change
    rclpy.spin(node)
    rclpy.shutdown()

if __name__=="__main__":
    main()
