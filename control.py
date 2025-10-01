import time
import matplotlib.pyplot as plt
import balltracker as bt
import numpy as np

class PIDControler():
    def __init__(self,setpoint,Kp,Ki,Kd,margin=20.0,pv=0) -> None:
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint # set point,aka goal
        self.margin = margin

        self.logging = False
        self.previous_error = 0
        self.integral = 0
        self.last_calc = time.time()
        self.past_variables =[pv]
        self.times=[0.0]
        self.dt = 0.0

    def compute(self,pv) :

        self.dt = time.time()-self.last_calc
        self.dt = min(max(self.dt, 1/120), 1/30) 
        if self.logging:
            self.past_variables.append(pv)
            self.times.append(self.times[-1]+self.dt)

        error = self.setpoint-pv
        P_out = error*self.Kp
        self.integral += error*self.dt
        I_out =self.Ki * self.integral
        derivative = (error - self.previous_error) / self.dt
        D_out = self.Kd * derivative

        output = P_out+I_out+D_out
        self.previous_error = error
        self.last_calc = time.time()
        return output

    def reached_setpoint(self,pv):
        if pv == self.setpoint:
            return True
        return pv < self.setpoint + self.margin and pv > self.setpoint - self.margin

    def reset(self):
        self.previous_error =0
        self.integral = 0
        self.times = [0.0]
        self.dt = 0.0
        self.last_calc = time.time()
        self.past_variables = [0]

    def plot(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.times, self.past_variables, label='Process Variable')
        plt.axhline(y=self.setpoint, color='r', linestyle='--', label='Setpoint')
        plt.xlabel('Time (s)')
        plt.ylabel('Process_variable')
        plt.title('PID Controller')
        plt.legend()
        plt.grid()
        plt.show()


class OpenLoop():
    def __init__(self,sv,pv,delta) -> None:
        self.delta = delta
        self.pv = pv
        self.sv = sv
    def set_pv(self,pv):
        self.pv = pv
        if self.pv > self.sv:
            self.delta = self.delta*-1

    def calculate(self):
        if self.pv == self.sv:
            self.delta = 0
        self.pv += self.delta
        return self.delta

def test_pid_temp():
    # Initialize PID controller
    setpoint = 100  # Desired temperature
    pid = PIDControler(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=setpoint,margin=0.01,pv=20)
    # Simulation parameters
    process_variable = 20  # Initial temperature

    # Simulate the process
    while not pid.reached_setpoint(process_variable):
        print(process_variable)
        # PID control output
        control_output = pid.compute(process_variable)

        # Simulate process dynamics (heating rate proportional to control output)
        process_variable += control_output * pid.dt - 0.1 * (process_variable - 20) * pid.dt  # Heat loss

        # Store the process variable
    # Plot results
    pid.plot()





if __name__ == "__main__":
    test_pid_temp()
