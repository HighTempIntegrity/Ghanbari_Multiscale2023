      ! Abaqus Subroutines:
      ! Purpose: Activating elements based on imported field variable
      SUBROUTINE UEPACTIVATIONVOL(LFLAGS,EPANAME,NOEL,NELEMNODES,
     1 IELEMNODES,MCRD,COORDNODES,UNODES,KSTEP,KINC,TIME,DTIME,
     2 TEMP,NPREDEF,PREDEF,NSVARS,SVARS,SOL,SOLINC,VOLFRACT,
     3 NVOLUMEADDEVENTS,VOLFRACTADDED,CSIADDED,ORI,EIGENSTRAINS)     
      ! Will be called at the beginning of each increment in a step in which element actiation is used
      ! at each element
      
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION LFLAGS(*),IELEMNODES(NELEMNODES),COORDNODES(MCRD,NELEMNODES),
     1 UNODES(MCRD,NELEMNODES),TIME(2),SVARS(NSVARS,2),TEMP(2,NELEMNODES),
     2 PREDEF(2,NPREDEF,NELEMNODES),SOL(NELEMNODES),SOLINC(NELEMNODES),
     3 VOLFRACT(*),VOLFRACTADDED(*),CSIADDED(3,*),ORI(3,3),EIGENSTRAINS(*)
      CHARACTER*80 EPANAME
      ! NELEMNODES: Number of element nodes.
      ! COORDNODES(MCRD,NELEMNODES): An array containting the coordinates of the nodes of the element
      ! NPREDEF: Number of field variables.
      ! PREDEF: An array containing pairs of values of predefined field variables at the element nodes
      !         predef(1,npredef,nElemNodes), corresponds to the value at the end of the increment
      ! volFract(1): element activation from previous increment
      
      ! User coding to define volfractadded
      ! and possibly update eigenstrains, lflags(4), ori, svars
      
      VOLFRACTADDED(1) = volFract(1)

      RETURN
      END
