      MODULE SHARED_VARS
      
      ! Printing parameters
      REAL*8, PARAMETER :: GTOL = 0.1D-3        ! Geomterical tolerance 0.1 μm
      REAL*8, PARAMETER :: THICKNESS = 30.D-3   ! mm
      REAL*8, PARAMETER :: DT_MIN = 5.D-5       ! Ideal time increment at center of ellipsoid
      REAL*8, PARAMETER :: DT_MAX = 2.D-3       ! Ideal time increment at boundary of ellipsoid
      ! Ellipsoid parameters
      REAL*8, PARAMETER :: REFINE_X = 5.D0      ! The ellipsoid size to initiate refinement in laser direction
      REAL*8, PARAMETER :: REFINE_Y = 1.D0   ! The ellipsoid size to initiate refinement in hatch direction
      REAL*8, PARAMETER :: REFINE_Z = 1.D0      ! The ellipsoid size to initiate refinement in build direction
      REAL*8, PARAMETER :: PROBE_LAYER = 1      ! The layer where increment adjustment begins
      REAL*8, PARAMETER, DIMENSION(3) :: PROBE_COORDS = (/5.0D0,0.D0,PROBE_LAYER*THICKNESS/)
      
      ! Code
      CHARACTER(*), PARAMETER :: LSREVNT = '1_AM_laser.inp'
      CHARACTER(*), PARAMETER :: COUTPUT = 'run_2track.csta'
      REAL*8, PARAMETER :: CTOL = 1.D-6     ! Calculation tolerance
    
      END MODULE SHARED_VARS
    
    
!====== Abaqus Subroutines ======!
      SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT,
     1 TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER,
     2 KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,LACCFLA)
      USE SHARED_VARS
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME,ORNAME
      CHARACTER*3  FLGRAY(15)
      DIMENSION FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),
     1 T(3,3),TIME(2)
      DIMENSION ARRAY(15),JARRAY(15),JMAC(*),JMATYP(*),COORD(*)
      !! My variables
      REAL*8 dt_ideal_cur,ratio_cur
      REAL*8,DIMENSION(3) :: laser_str, laser_end, temp_coords, laser_cur
      LOGICAL :: state_str,state_end,state_cur
      INTEGER :: i, num=2000
      
      !! Common block
      LOGICAL :: laser_switch(2)
      REAL*8  :: dt_ratio, dt_ideal_min, layerNo_end
      INTEGER :: pre_kinc
      COMMON /com_vars/ laser_switch,
     1 dt_ratio, dt_ideal_min, layerNo_end,
     2 pre_kinc
      
      ! Run the calculations only for the 1st integration point
      IF (NPT.GT.1.D0) THEN
        RETURN
      END IF
      
      ! Parameter initialization
      CALL LASER_POSITION(TIME(2),laser_str,state_str)
      CALL LASER_POSITION(TIME(2)+DTIME,laser_end,state_end)
      CALL TARGET_DT(laser_end,dt_ideal_min)
      layerNo_end = laser_end(3)/THICKNESS
      
      IF (laser_end(3).GT.PROBE_COORDS(3)-GTOL) THEN ! While past the probe layer
        IF (laser_str(3).LT.PROBE_COORDS(3)-GTOL) THEN ! If the start is still below the layer
            ! Cutback to the limit
            DO
                READ (101,*,IOSTAT=ios) time_tmp, temp_coords(1), temp_coords(2), temp_coords(3)
                IF (ABS(temp_coords(3)-PROBE_COORDS(3)).LT.GTOL) THEN
                    EXIT
                END IF
                pre_time_tmp = time_tmp
                IF (ios /= 0) EXIT
            END DO
            REWIND(101)
            PNEWDT=ABS(time_tmp-TIME(2))/DTIME
        ELSE IF (laser_end(3).GT.PROBE_COORDS(3)+THICKNESS-GTOL .AND.
     1           .NOT. laser_switch(1)) THEN ! If the end has goes over the probe layer
            PNEWDT = 0.1
        ELSE
            laser_switch(1) = .TRUE.
        END IF
        
        IF (laser_switch(1)) THEN ! While we are in the layer
            ratio_cur = 1.D0
            ! Numerical minimization over the path segment
            DO i = 0,num
                time_cur = TIME(2)+DTIME*i/num
                CALL LASER_POSITION(time_cur,laser_cur,state_cur)
                CALL TARGET_DT(laser_cur,dt_ideal_cur)
                CALL NEW_DT(dt_ideal_cur,DTIME,ratio_cur)
                IF (state_cur .AND. ratio_cur.LT.PNEWDT) THEN
                    PNEWDT = ratio_cur
                    dt_ideal_min = dt_ideal_cur
                END IF
            END DO
        END IF
      END IF ! Past the probe layer

      dt_ratio=PNEWDT

      RETURN
      END
           
      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      USE SHARED_VARS
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION TIME(2)
      !! My variables
      CHARACTER*256 OUTDIR
      
      !! Common block
      LOGICAL :: laser_switch(2)
      REAL*8  :: dt_ratio, dt_ideal_min, layerNo_end
      INTEGER :: pre_kinc
      COMMON /com_vars/ laser_switch,
     1 dt_ratio, dt_ideal_min, layerNo_end,
     2 pre_kinc
    
      ! LOP = 0; start of analysis
      ! LOP = 1; start of increment
      ! LOP = 2; end of increment
      ! LOP = 3; end of analysis
      ! LOP = 4; start of restart
      ! LOP = 5; start of step
      ! LOP = 6; end of step
      
      ! Start of analysis
      IF (LOP.EQ.0) THEN
        CALL GETOUTDIR( OUTDIR, LENOUTDIR )
        OPEN(101, FILE=TRIM(OUTDIR)//'/'//LSREVNT)    ! Open laser event series file
        OPEN(102, FILE=TRIM(OUTDIR)//'/'//COUTPUT)    ! Open (create) custom status file
        WRITE(102,'(A2,1A,1X,A6,1A,1X,A10,1A,1X,A14,1A,1X,A10,1A,1X,A10,1A,1X,A9,1A,1X,A5)')
     1            'KS',',','KINC',',','TIME(1)',',','TIME(2)',',','DTIME',',','DT_IDEAL',',','PNEWDT',',','LAYER'
        
        pre_kinc = 0
        ! USDFLD initialization
        laser_switch(1) = .FALSE. ! Switch for that we are in the layer;
      END IF
      
      ! Start of increment
      IF (LOP.EQ.1) THEN
        WRITE(102,'(I2,1A,1X,I4,A2,1A,1X,F10.6,1A,1X,F14.10,1A,1X,ES10.3,1A,1X,ES10.3,1A,1X,F9.4,1A,1X,F5.0)')
     1            KSTEP,',',KINC,'_S',',',TIME(1),',',TIME(2),',',DTIME,',',dt_ideal_min,',',dt_ratio,',',layerNo_end
        WRITE(*,'(A,F10.6,4X,A,I4)') 'Time:',TIME(2),' KINC:',KINC
      END IF
      
      ! End of increment
      IF (LOP.EQ.2) THEN
        WRITE(102,'(I2,1A,1X,I4,A2,1A,1X,F10.6,1A,1X,F14.10,1A,1X,ES10.3,1A,1X,ES10.3,1A,1X,F9.4,1A,1X,F5.0)')
     1            KSTEP,',',KINC,'_E',',',TIME(1),',',TIME(2),',',DTIME,',',dt_ideal_min,',',dt_ratio,',',layerNo_end
      END IF
      
      ! End of analysis
      IF (LOP.EQ.3) THEN
        CLOSE(101)  ! Close the laser event series file
        CLOSE(102)  ! Close custom status file
      END IF
      
      RETURN
      END


!====== Custom Subroutines ======!
      SUBROUTINE LASER_POSITION(TIME,LASER_COORDS,LASER_STATE)
      USE SHARED_VARS
      INCLUDE 'ABA_PARAM.INC'
      REAL*8,   INTENT(IN)  :: 
     1          TIME
      REAL*8,DIMENSION(3),INTENT(OUT) ::
     1          LASER_COORDS(3)
      LOGICAL,  INTENT(OUT) ::
     1          LASER_STATE
      REAL*8 cur_time,cur_x,cur_y,cur_z,cur_power,
     1       pre_time,pre_x,pre_y,pre_z,pre_power
      
      DO
        READ (101,*,IOSTAT=ios) cur_time, cur_x, cur_y, cur_z, cur_power ! File is opnened through UEXTERNALDB
        IF (TIME.LT.cur_time) THEN
            EXIT
        END IF
        pre_time = cur_time
        pre_x = cur_x
        pre_y = cur_y
        pre_z = cur_z
        pre_power = cur_power
        IF (ios /= 0) EXIT
      END DO
      REWIND(101)
      
      LASER_COORDS(1) = pre_x+(TIME-pre_time)/(cur_time-pre_time)*(cur_x-pre_x)
      LASER_COORDS(2) = pre_y+(TIME-pre_time)/(cur_time-pre_time)*(cur_y-pre_y)
      LASER_COORDS(3) = pre_z+(TIME-pre_time)/(cur_time-pre_time)*(cur_z-pre_z)
      
      LASER_STATE = .TRUE.
      IF (ABS(pre_power-0.D0).LT.CTOL) THEN
        LASER_STATE = .FALSE.
      END IF
      
      RETURN
      END
      
      
      SUBROUTINE TARGET_DT(POINT,DT_I)
      USE SHARED_VARS
      INCLUDE 'ABA_PARAM.INC'
      REAL*8,INTENT(IN) :: 
     1 POINT(3)
      REAL*8,INTENT(OUT) ::
     1 DT_I
     
      DT_I = (((POINT(1)-PROBE_COORDS(1))/REFINE_X)**2
     1       +((POINT(2)-PROBE_COORDS(2))/REFINE_Y)**2
     2       +((POINT(3)-PROBE_COORDS(3))/REFINE_Z)**2)
     3       *(DT_MAX-DT_MIN)+DT_MIN

      RETURN
      END
      
      
      SUBROUTINE NEW_DT(DT_I,DT_C,RATIO)
      INCLUDE 'ABA_PARAM.INC'
      REAL*8,INTENT(IN) :: 
     1 DT_I,DT_C
      REAL*8,INTENT(OUT) ::
     1 RATIO
      
      RATIO = DT_I/DT_C
      IF (RATIO.GT.0.9D0 .AND. RATIO.LT.1.D0) THEN
        RATIO = 1.D0
      ELSE IF (RATIO.LT.0.1D0) THEN
        RATIO = 0.1D0
      END IF
      
      RETURN
      END
