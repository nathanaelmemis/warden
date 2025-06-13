import { Box, type BoxProps } from "@mui/material"

export function Background(props: BoxProps) {
    const { children } = props

    return (
        <Box
            {...props}
            height="100vh"
            sx={{
                backgroundColor: "primary.dark"
            }}
        >
            {children}
        </Box>
    )
}