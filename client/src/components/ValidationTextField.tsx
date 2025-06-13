import { TextField, type TextFieldProps } from "@mui/material"
import { useState, type FC, type Dispatch, type SetStateAction, type ChangeEvent } from "react"

type ValidationTextFieldProps = {
    value: string,
    setValue: (value: string) => void
    pattern?: RegExp
} & TextFieldProps

export const ValidationTextField: FC<ValidationTextFieldProps> = (props) => {
    const { value, setValue, pattern } = props
    const [error, setError] = useState(false)

    const handleValueChange = (event: ChangeEvent<HTMLInputElement>) => {
        setValue(event.target.value)
        setError(!!pattern && !event.target.value.match(pattern))
    }

    return (
        <TextField
            {...props}
            value={value}
            onChange={handleValueChange}
            error={error}
        />
    )
}